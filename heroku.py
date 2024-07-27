async def en_download(event, args, client):
    """
    Downloads the replied message: to a location (specified) locally
    Available arguments:
      End the args with '/' to specify the folder in which to download and let the bot use its filename
      or:
        --dir DIR (Must be in double quotes.)
        --home (To download to current working directory.)
      --cap (To use download with caption instead of filename.)
      if no other arg is given after dir, bot automatically downloads to given dir with default filename instead.

      *path specified directly will be downloaded as a subdir to download folder
    """
    if not user_is_owner(event.sender_id):
        return await event.delete()
    if not event.is_reply:
        return await event.reply("`Reply to a file or link to download it`")
    try:
        _dir = None
        loc = None
        link = None
        rep_event = await event.get_reply_message()
        message = await client.get_messages(event.chat_id, int(rep_event.id))
        if message.text and not (is_url(message.text) or is_magnet(message.text)):
            return await message.reply("`Not a valid link`")
        e = await message.reply(f"{enmoji()} `Downloading…`", quote=True)
        if args is not None:
            arg, args = get_args(
                ["--home", "store_true"],
                ["--cap", "store_true"],
                "--dir",
                to_parse=args,
                get_unknown=True,
            )
            if args.endswith("/"):
                _dir = args
            else:
                loc = args
            if arg.home:
                _dir = home_dir
            elif arg.dir:
                _dir = arg.dir
            if arg.cap and not message.text:
                loc = message.caption
        link = message.text if message.text else link
        if not loc:
            loc = rep_event.file.name if not link else link
        _dir = "downloads/" if not _dir else _dir
        _dir += str() if _dir.endswith("/") else "/"
        await try_delete(event)
        d_id = f"{e.chat.id}:{e.id}"
        download = downloader(_id=d_id, uri=link, folder=_dir)
        await download.start(loc, 0, message, e)
        if download.is_cancelled or download.download_error:
            return await report_failed_download(
                download, e, download.file_name, event.sender_id
            )
        f_loc = _dir + loc if not link else _dir + download.file_name
        new_file_name = "video.mp4"
        new_f_loc = os.path.join(os.path.dirname(f_loc), new_file_name)
        os.rename(f_loc, new_f_loc)
        f_loc = new_f_loc
        await e.edit(f"__Saved to__ `{f_loc}` __successfully!__")
    except Exception:
        await logger(Exception)
