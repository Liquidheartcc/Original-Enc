sut = time.time()
fname = path_split(out)[1]
pcap = await custcap(name, fname, ver=v, encoder=conf.ENCODER, _filter=f)
await op.edit(f"`Uploading…` `{out}`") if op else None

try:
    # Check file size
    size_of_file = os.path.getsize(out)
    if size_of_file > 2126000000:  # 2126000000 bytes ≈ 2GB
        folder_id = '1B7B15U7a14mWpPKvKvMe6vRXAg10zpL2'
        try:
            download_url = upload_to_gdrive(out, folder_id)
            chain_msg = await reply_message(
                message=message,
                text=f"File `{out}` is larger than 2GB. Uploaded to Google Drive: {download_url}",
                quote=True,
            )
        except Exception as e:
            chain_msg = await reply_message(
                message=message,
                text=f"Uploading of `{out}` to Google Drive failed: {str(e)}",
                quote=True,
            )
        # Ensure task completion
        skip(queue_id)
        mark_file_as_done(einfo.select, queue_id)
        await save2db()
        await save2db("batches")
    else:
        upload = uploader(sender_id, _id)
        up = await upload.start(msg_t.chat_id, out, msg_p, thumb2, pcap, message)
        if upload.is_cancelled:
            m = f"`Upload of {out} was cancelled`"
            if sender_id != upload.canceller:
                canceller = await pyro.get_users(upload.canceller)
                m += f" by {canceller.mention()}"
            m += "!"
            await msg_p.edit(m)
            if op:
                await op.edit(m)
            skip(queue_id)
            mark_file_as_done(einfo.select, queue_id)
            await save2db()
            await save2db("batches")
            if download:
                await download.clean_download()
            s_remove(thumb2, dl, out)
            return
        
        eut = time.time()
        utime = tf(eut - sut)

        await msg_p.delete()
        await op.delete() if op else None
        await up.copy(chat_id=log_channel) if op else None

        org_s = size_of(dl)
        out_s = size_of(out)
        pe = 100 - ((out_s / org_s) * 100)
        per = str(f"{pe:.2f}") + "%"
        mux_msg = f"Muxed in `{mtime}`\n" if mux_args else str()

        mi = await info(dl)
        mi2 = await info(out)
        forward_task = asyncio.create_task(forward_(name, out, up, mi, f))

        text = f""
        if mi:
            text += f"\n\n🎞️ **Mediainfo:** **[(Source)]({mi})** | **[(Encoded)]({mi2})**"
        else:
            text += f"\n\n🎞️ **Mediainfo:** **N/A**"

        st_msg = await up.reply(
            f"🚀 **Encode Stats:**\n\nOriginal Size: "
            f"`{hbs(org_s)}`\nEncoded Size: `{hbs(out_s)}`\n"
            f"Encoded Percentage: `{per}`\n\n"
            f"{'Cached' if einfo.cached_dl else 'Downloaded'} in `{dtime}`\n"
            f"Encoded in `{etime}`\n{mux_msg}Uploaded in `{utime}`"
            f"{text}",
            disable_web_page_preview=True,
            quote=True,
        )
        await st_msg.copy(chat_id=log_channel) if op else None
        await forward_task

        skip(queue_id)
        mark_file_as_done(einfo.select, queue_id)
        await save2db()
        await save2db("batches")
        s_remove(thumb2)
        if download:
            await download.clean_download()
        s_remove(dl, out)

except Exception as e:
    await logger(e)
    error = (
        "Due to an unknown error "
        "bot has been paused indefinitely\n"
        "check logs for more info."
    )
    l_msg = await bc_msg(error)
    entime.pause_indefinitely(l_msg)

finally:
    einfo.reset()
    await asyncio.sleep(5)
