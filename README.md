# Computer and Network Security Project (COMP 5370/6370)

**Project:** Secure File Sharing System

**Team Members:** Lanie Louque, Grayson Morgan, Laura Joy Simpson, and Courtney Lin

## Project Overview

The Secure File Sharing System is an academic project designed to support file transfers over a Local Area Network (LAN). It uses FastAPI to provide HTTP endpoints and SQLite to store user records, file metadata, file-sharing permissions, and audit logs.

The current implementation focuses on file uploads and downloads, file validation, SHA-256 checksum verification, and database operations.

## Deliverable 1: Implemented Features

The current implementation includes:

- **File uploads:** Accepts files through an HTTP endpoint and stores them on the server.
- **File downloads:** Allows users to download files using a unique file UUID.
- **SHA-256 checksums:** Calculates a checksum when a file is uploaded and verifies the checksum when the file is prepared for download.
- **File validation:** Checks that an uploaded file exists, has an allowed extension, and does not exceed the size limit.
- **SQLite database:** Stores user records, file metadata, checksums, sharing permissions, and audit records.
- **Audit logging:** Records successful upload and download operations.

## Planned Features for Deliverable 2

The following features are planned for Deliverable 2:

- **Identity and Access Control**
  - User account creation and deletion through application endpoints.
  - User login and authentication.
  - Password changing.
  - File sharing and access permissions between users.

Some supporting database functions for account management and file sharing are already present. However, the current FastAPI application does not expose all these functions through HTTP endpoints, and it does not implement a complete login or authentication workflow.

## Project Structure

The repository contains the following files:

```text
Computer-and-Network-Security-Project-1/
├── database_files/
│   ├── __init__.py
│   ├── db_main.py
│   └── db_operations.py
├── main.py
├── validation.py
├── .gitignore
└── README.md
```

The application creates these directories and files when initialized or run:

```text
Computer-and-Network-Security-Project-1/
├── database_files/
│   └── filesharing.db
├── server_uploaded_files/
└── downloaded_files/
```

- `main.py` — Defines the FastAPI application and HTTP endpoints.
- `validation.py` — Implements file-validation rules.
- `database_files/db_main.py` — Establishes SQLite connections and creates the required directories.
- `database_files/db_operations.py` — Implements database operations for users, files, checksums, sharing permissions, and audit logs.
- `database_files/filesharing.db` — SQLite database created during initialization.
- `server_uploaded_files/` — Stores uploaded files on the server, using generated UUIDs as filenames.
- `downloaded_files/` — Temporary server-side destination used to prepare files for download.

The database and storage files are generated at runtime and are not required to be present in a fresh clone.

## Requirements

- Python 3.11 or newer recommended
- pip
- A terminal or command prompt
- Network access for testing from another computer on the same LAN

## Setup Instructions

Follow these steps from a fresh clone of the repository.

### 1. Clone the repository

```bash
git clone https://github.com/clin052023/Computer-and-Network-Security-Project-1.git
cd Computer-and-Network-Security-Project-1
```

Alternatively, download the repository as a ZIP file, extract it, and open a terminal in the extracted project directory.

### 2. Install dependencies

Run:

```bash
python -m pip install fastapi uvicorn python-multipart
```

If your system uses `python3` instead of `python`, use `python3` in place of `python` in the commands below.

### 3. Initialize the database

Run this command from the project root:

```bash
python -c "from database_files import get_connection, db_operations; conn = get_connection(); db_operations.create_db(conn); db_operations.create_user_account(conn, 'grader', 'demo-hash-placeholder'); conn.close()"
```

This command:

1. Creates the SQLite database and its tables.
2. Creates a demonstration user record named `grader`.
3. Closes the database connection.

**Important:** `demo-hash-placeholder` is a placeholder value, not a real password hash. The current application does not provide a login endpoint. The username is used by the existing upload and download endpoints to associate file operations with a database user; it does not authenticate the caller.

If you run the command again, the existing tables are retained and the account-creation function reports that `grader` already exists.

### 4. Start the server

From the project root, run:

```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Keep the terminal open while testing the application.

The API should be accessible at:

- **Local API:** `http://127.0.0.1:8000`
- **Interactive API documentation:** `http://127.0.0.1:8000/docs`

## Testing the Application

### Upload a file

The application accepts the following file extensions:

- `.pdf`
- `.docx`
- `.png`
- `.jpg`
- `.jpeg`

The maximum permitted file size is 100 MB.

Place a supported test file in your current directory. For example, if the file is named `sample.pdf`, run:

```bash
curl -F "file=@sample.pdf" "http://127.0.0.1:8000/upload/?username=grader"
```

On Windows PowerShell, use `curl.exe` instead of `curl` if `curl` is interpreted as a PowerShell alias.

A successful upload returns a response similar to:

```json
{
  "message": "File uploaded successfully",
  "uuid": "YOUR_FILE_UUID"
}
```

The UUID above is a placeholder. Copy the actual UUID returned by the server for the next step.

### Download a file

Replace `YOUR_FILE_UUID` with the UUID returned by the upload request:

```bash
curl -L "http://127.0.0.1:8000/download/YOUR_FILE_UUID?username=grader" -o downloaded_sample.pdf
```

This saves the downloaded file as `downloaded_sample.pdf` in your current directory.

Use the appropriate file extension for the file you uploaded.

### Verify the file transfer

After downloading, compare the original and downloaded files. Their SHA-256 checksums should match if the files are identical.

On Windows PowerShell, run:

```powershell
Get-FileHash .\sample.pdf -Algorithm SHA256
Get-FileHash .\downloaded_sample.pdf -Algorithm SHA256
```

Replace the filenames with your actual filenames if they differ.

On Linux or macOS, run:

```bash
sha256sum sample.pdf downloaded_sample.pdf
```

The two checksums should be identical.

## Testing Through the API Documentation

FastAPI provides an interactive interface for testing the endpoints.

1. Start the server.
2. Open `http://127.0.0.1:8000/docs` in a browser.
3. Expand `POST /upload/` and select **Try it out**.
4. Enter `grader` as the username and select a supported file.
5. Execute the request and copy the returned UUID.
6. Expand `GET /download/{file_uuid}` and select **Try it out**.
7. Enter the UUID and the username `grader`.
8. Execute the request and inspect the response.

## Instructions for Graders

To verify the current file-transfer functionality:

1. Clone or download the repository.
2. Install the required dependencies.
3. Initialize the database using the command provided above.
4. Start the server on port 8000.
5. Open `http://127.0.0.1:8000/docs`.
6. Upload a supported test file using `POST /upload/`.
7. Copy the UUID returned by the server.
8. Download the file using `GET /download/{file_uuid}`.
9. Compare the downloaded file with the original to verify the transfer.

### Testing from another computer on the LAN

To test from a second computer:

1. Start the server on the host computer using the command above.
2. Find the host computer's LAN IP address.
3. Ensure the host firewall permits inbound connections on port 8000.
4. From the second computer, replace `127.0.0.1` in the example URLs with the host computer's LAN IP address.

For example, if the host's LAN IP address is `192.168.1.100`, open:

```text
http://192.168.1.100:8000/docs
```

The address above is only an example. Use the actual LAN IP address of the server host.

## Troubleshooting

### The server does not start

- Confirm that the terminal is in the project root.
- Verify that Python is installed.
- Install the required dependencies.
- Check whether port 8000 is already in use.

### The database or tables are missing

- Run the database initialization command from the project root.
- Confirm that `database_files/__init__.py`, `database_files/db_main.py`, and `database_files/db_operations.py` exist.

### The upload fails

- Confirm that the server is running.
- Check that the file extension is supported.
- Ensure the file does not exceed 100 MB.
- Confirm that the username exists in the database.
- Review the HTTP error response and server terminal output.

### The download fails

- Confirm that the UUID came from a successful upload.
- Use the same username supplied during upload, unless the file has been shared with another existing user through the database operations.
- Check the server terminal for error messages.
- Confirm that the stored file still exists on the server.

### Another computer cannot connect

- Confirm that both computers are connected to the same LAN.
- Use the server host's LAN IP address instead of `127.0.0.1`.
- Check firewall settings and ensure port 8000 is permitted.

## Security Notes and Limitations

This project is an academic prototype and is not intended for production deployment.

- The API accepts a username as a request parameter; this does not verify the caller's identity.
- A complete login and authentication workflow is not implemented in the current API.
- A placeholder account password value must not be treated as a secure credential.
- Database functions for user management and file sharing are not all exposed through HTTP endpoints.
- The development server does not configure HTTPS or provide comprehensive production security hardening.
- Do not expose this development server to the public internet.

These limitations should be addressed before using the application to store or transfer sensitive files in a real-world environment.