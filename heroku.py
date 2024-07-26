async def enleech(event, args: str, client, direct=False):
    try:
        if event.is_reply:
            rep_event = await event.get_reply_message()
            if rep_event.file:
                await event.reply("**Warning:** `Use /add for files instead.`")
                return await addqueue(event, o_args, client)
            if args:
                # Split the args to get the URL and the new file name
                args_list = args.split(' ', 1)
                url = args_list[0]
                new_file_name = args_list[1] if len(args_list) > 1 else None

                if not url.isdigit():
                    return await event.reply(
                        f"**Yeah No.**\n`Error: expected a number but received '{url}'.`"
                    )
                args = int(url)
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
                        
                        # Rename the file if a new file name is provided
                        if new_file_name:
                            file.name = new_file_name

                        # Continue with the rest of your processing
                        # ...

except Exception as e:
        await event.reply(f"**Error:** `{str(e)}`")
