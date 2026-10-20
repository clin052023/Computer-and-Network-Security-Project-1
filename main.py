'''
 ------------------------------------
|              main.py               |
|                 ---                |
|    HTTP and SQLite Connection ---  |
 ------------------------------------

 The format of the app is like this:

 - Uploaded files are stored on the server's end.
 - Clients need to make requests to interact with the server through HTTP.
    - Add encryption later !
 - Clients store downloaded files in a folder on their own device.

'''

# Download FastAPI and Uvicorn

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pathlib import Path
import tempfile
import sqlite3 

# Importing local files

from database_files import get_connection, db_operations
from contextlib import asynccontextmanager
import validation

# Project folders
PROJECT_ROOT = Path(__file__).resolve().parent
DOWNLOAD_DIR = PROJECT_ROOT / "downloaded_files"
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MiB

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create the download directory if it doesn't exist
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    conn = get_connection()
    try:
        # Initialize the database tables if they don't exist
        db_operations.create_db(conn)
    finally:
        conn.close()

    yield

# Create the FastAPI app
app = FastAPI(lifespan=lifespan)

# Upload a file to the server
@app.post("/upload/")
async def upload_file(username: str, file: UploadFile):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    upload_path = None

    try:
        # Save the incoming file to a temporary location
        suffix = Path(file.filename).suffix

        with tempfile.NamedTemporaryFile(
            suffix=suffix, delete=False
        ) as temp_file:
            upload_path = Path(temp_file.name)

            # Read and save the uploaded file in chunks
            total_size = 0
            while True:
                chunk = await file.read(1024 * 1024)

                if not chunk:
                    break
               
                total_size += len(chunk)


                if total_size > MAX_FILE_SIZE:
                    raise HTTPException(status_code=413, detail="File size exceeds 100 MiB limit.")

                temp_file.write(chunk)

        # Validate the file before storing it
        valid, message = validation.validate_file(upload_path)

        if not valid:
            raise HTTPException(status_code=400, detail=message)

        # Save the file and its metadata through the database function
        conn = get_connection()

        try:
            file_uuid = db_operations.upload_file(
                conn, username, upload_path, file.filename
            )
        finally:
            conn.close()

        if not file_uuid:
            raise HTTPException(
                status_code=400,
                detail="Upload failed. Check that the username exists."
            )

        return {
            "message": "File uploaded successfully",
            "uuid": file_uuid,
            "filename": file.filename,
            "size": total_size
        }

    finally:
        # Remove the temporary file
        if upload_path is not None:
            upload_path.unlink(missing_ok=True)

        await file.close()


# Download a file from the server
@app.get("/download/{file_uuid}")
def download_file(file_uuid: str, username: str):
    conn = get_connection()

    # Use the existing database function to check access,
    # copy the file, and verify its checksum
    try:
        download_path = db_operations.download_file(
            conn, username, file_uuid
        )
    finally:
        conn.close()

    if download_path is None or not download_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Download failed. File not found or access denied."
        )

    # Get the original filename from the database for the HTTP response
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM File_Metadata WHERE uuid = ?",
            (file_uuid,)
        )
        file_row = cursor.fetchone()
    finally:
        conn.close()

    if file_row is None:
        raise HTTPException(
            status_code=404, detail="File metadata not found."
        )

    filename = Path(file_row["name"]).name

    # Send the file to the client
    return FileResponse(
        path=download_path,
        filename=filename,
        media_type="application/octet-stream"
    )
