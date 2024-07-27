async def enleech(event, args: str, client, direct=False):
    """
    Adds a link or torrent link to encoding queue:
        Requires a reply to link or the link as argument
        can also add consecutive items to queue by replying
        to the first link and a number of how many links to add to queue
    Accepts the following flags:
        -f filter (only use if familiar with filter format)
        -rm what_to_remove (keyword to remove from torrent file_name)
        -tc caption_tag (tag caption type as…)
        -tf file_tag (tag file_as)
        -v number (tag according to version number)
    Both flags override /filter & /v

    :: filter format-
        what_to_remove\\ntag_file_as\\ntag_caption_as
    ::
    """
    chat_id = event.chat_id
    user_id = event.sender_id
    if not (user_is_allowed(user_id) or direct):
        return
    cust_fil = cust_v = str()
    mode = "None"
    o_args = None
    queue = get_queue()
    invalid_msg = "`Invalid torrent/direct link`"
    no_uri_msg = (
        "`uhm you need to reply to or send command alongside a uri/direct link`"
    )
    no_dl_spt_msg = "`File to download is…\neither not a video\nor is a batch torrent which is currently not supported.`"
    ukn_err_msg = "`An unknown error occurred, might an internal issue with aria2.\nCheck logs for more info`"
    if args:
        o_args = args
        flag, args = get_args(
            "-f", "-rm", "-tc", "-tf", "-v", to_parse=args, get_unknown=True
        )
        if flag.rm or flag.tc or flag.tf:
            cust_fil = flag.rm or "disabled__"
            cust_fil += str().join(
                f"\n{x}" if x else "\nauto" for x in [flag.tf, flag.tc]
            )
        else:
            cust_fil = str_esc(flag.f)
        cust_v = flag.v
    try:
        if event.is_reply:
            rep_event = await event.get_reply_message()
            if rep_event.file:
                await event.reply("**Warning:** `Use /add for files instead.`")
                return await addqueue(event, o_args, client)
            if args:
                if not args.isdigit():
                    return await event.reply(
                        f"**Yeah No.**\n`Error: expected a number but received '{args}'.`"
                    )
                args = int(args)
                async with queue_lock:
                    for _none, _id in zip(
                        range(args), itertools.count(start=rep_event.id)
                    ):
                        event2 = await client.get_messages(event.chat_id, _id)
                        if event2.empty:
                            await event.reply(
                                f"Resend uri links and try replying the first with /l or /leech again"
                            )
                            return await rm_pause(dl_pause, 5)
                        uri = event2.text
                        if not uri:
                            return await event.reply(no_uri_msg)
                        if not (is_url(uri) or is_magnet(uri)):
                            await event2.reply(invalid_msg)
                            return await rm_pause(dl_pause, 5)
                        file = await get_leech_name(uri)
                        if file.error:
                            await event2.reply(f"`{file.error}`", quote=True)
                            await asyncio.sleep(10)
                            continue
                        if not is_video_file(file.name):
                            await event2.reply(no_dl_spt_msg, quote=True)
                            await asyncio.sleep(5)
                            continue
                        already_in_queue = False
                        for item in queue.values():
                            if file.name in item:
                                await event2.reply(
                                    "**THIS LINK HAS ALREADY BEEN ADDED TO QUEUE**",
                                    quote=True,
                                )
                                await asyncio.sleep(5)
                                already_in_queue = True
                                break
                        if already_in_queue:
                            continue
                        if not bot_is_paused():
                            pause(status=dl_pause)

                        queue.update(
                            {
                                (chat_id, event2.id): [
                                    file.name,
                                    (user_id, event2),
                                    (
                                        cust_v or get_v(),
                                        cust_fil or get_f(),
                                        ("aria2", mode),
                                    ),
                                ]
                            }
                        )
                        await save2db()

                        msg = await event2.reply(
                            f"**Added to queue ⏰, POS:** `{len(queue)-1}`\n`Please Wait , Encode will start soon`",
                            quote=True,
                        )
                        await asyncio.sleep(5)
                    if len(queue) > 1:
                        asyncio.create_task(listqueue(msg, None, event.client, False))
                    return await rm_pause(dl_pause)
            else:
                uri = rep_event.text
                event = rep_event
        else:
            uri = args

        if not uri:
            return await event.reply(no_uri_msg)
        if not (is_url(uri) or is_magnet(uri)):
            return await event.reply(invalid_msg)
        file = await get_leech_name(uri)
        if file.error:
            return await event.reply(f"`{file.error}`")
        if not is_url(uri):
            return await event.reply(no_dl_spt_msg)
        
        async with queue_lock:
            queue.update(
                {
                    (chat_id, event.id): [
                        file.name,
                        (user_id, None),
                        (cust_v or get_v(), cust_fil or get_f(), ("aria2", mode)),
                    ]
                }
            )
            await save2db()
        if len(queue) > 1 or bot_is_paused():
            msg = await event.reply(
                f"**Added To Queue ⏰, POS:** `{len(queue)-1}`\n`Please Wait , Encode will start soon`"
            )
            if len(queue) > 1:
                return asyncio.create_task(listqueue(msg, None, event.client, False))
    except Exception as e:
        await logger(Exception)
        await rm_pause(dl_pause)
        return await event.reply(f"An error Occurred:\n - {e}")
