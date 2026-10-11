'''
 ----------------------------------
|            db_main.py            |
|               ---                |
|    Database Connection File ---  |
 ----------------------------------

The DB should be installed onto the file manager's device over a Local Area Network.

The DB tracks file paths on users devices (ideally in an app specific folder like 'uploaded_files')
so that users on the same LAN can share files to each other through a centralized server.

The database should be named "filesharing.db".
This file establishes the connection from Python to the database.
'''

import sqlite3
from pathlib import Path

# The project only has a root directory and a subdirectory called 'database_files'.
# The SQLite database will be put in the subdirectory 'database_files' for organization.

PROJECT_ROOT = Path(__file__).resolve().parents[1]       # Only tracks .../project root directory/...
DB_DIR = PROJECT_ROOT / "database_files"                # Appends subdirectory 'database_files' to the root directory path
DATABASE_PATH = DB_DIR / "filesharing.db"               # Database path --- .../root/database_files/filesharing.db
UPLOAD_DIR = PROJECT_ROOT / "server_uploaded_files"            # Directory for files uploaded to the database, on server side
DOWNLOAD_DIR = PROJECT_ROOT / "downloaded_files"        # Destination directory for files downloaded from the database, on client side

def get_connection():

    # Ensures that '/root/database_files/' exists before trying to connect
    # Also makes sure that the upload and download directories exist as well

    DB_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # Creates a connection to the SQLite database, with a 10 second timeout before throwing an error.
    # If the database file does not exist, it will be created automatically in .../root/database_files/filesharing.db

    conn = sqlite3.connect(DATABASE_PATH, timeout=10)

    conn.execute("PRAGMA foreign_keys = 1")     # Enable foreign key support
    conn.execute("PRAGMA journal_mode = WAL")   # Enable "Write-Ahead Logging" for better concurrency, aka. read and write at the same time.
    conn.row_factory = sqlite3.Row              # This allows us to access columns by name instead of index
    return conn
