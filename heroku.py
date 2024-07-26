def upload_to_gdrive(file_path, folder_id):
    """Uploads a file to Google Drive and returns the web view link."""
    creds = None
    if os.path.exists(TOKEN_PICKLE_FILE_PATH):
        with open(TOKEN_PICKLE_FILE_PATH, 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PICKLE_FILE_PATH, 'wb') as token:
            pickle.dump(creds, token)
    service = build('drive', 'v3', credentials=creds)
    file_mimetype, _ = mimetypes.guess_type(file_path)
    media = MediaIoBaseUpload(open(file_path, 'rb'), mimetype=file_mimetype, resumable=True)
    file_metadata = {
        'name': os.path.basename(file_path),
        'parents': [folder_id],
        'mimeType': file_mimetype
    }
    file = service.files().create(body=file_metadata, media_body=media, fields='id,webViewLink').execute()
    return file.get("webViewLink")
