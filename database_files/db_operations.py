'''
 ----------------------------------
|         db_operations.py         |
|               ---                |
|    Database Operations File ---  |
 ----------------------------------

 Separate file for database operations to call while the app is running.
'''

# ------------------- #
#    IMPORTANT!!!     #
# ------------------- #
# Right now, these operations are only written to work *locally*
# We need to modify them to work over LAN after we establish HTTP endpoints
# My guess rn is that the upload/download functions need to be modified to work with FastAPI
# The other functions can probably work fine,,, it's mostly on the server's side doing work.

import sqlite3
import os
from pathlib import Path
import shutil
import uuid
import hashlib

# From db_main.py...
PROJECT_ROOT = Path(__file__).resolve().parents[1]
UPLOAD_DIR = PROJECT_ROOT / "server_uploaded_files"
DOWNLOAD_DIR = PROJECT_ROOT / "downloaded_files"


# ----------------------- # //////////////////////////////////////////////////////////////////////////
#     Create Database     # //////////////////////////////////////////////////////////////////////////
# ----------------------- # //////////////////////////////////////////////////////////////////////////

# Function to create the database and initializes tables if they don't exist yet.
# The database should be named "filesharing.db" and have the tables 'Users', 'File_Metadata', 
# and 'Audit_Log' as we have defined in the schema.
# An additional table 'File_Users_Shared_To' is a separate table made to store the UIDs of users
# that the owner has shared access to a specific files to.

def create_db(conn):

    cursor = conn.cursor()

    # Creates 'Users' table if it doesn't already exist
    # Autoincrement UID so that no UID is ever reused, even if a user is deleted.
    # Each username must be unique.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Users (
            uid INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL
        );
    """)

    # Creates 'File_Metadata' table if it doesn't already exist
    # File UUID is a randomly generated sequence in Python, so I save it as TEXT here.
    # Files belonging to a deleted user will all be deleted.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS File_Metadata (
            uuid TEXT PRIMARY KEY,
            owner_uid INTEGER NOT NULL,
            name TEXT NOT NULL,
            location_path TEXT NOT NULL,
            size INTEGER NOT NULL,
            type TEXT NOT NULL,
            SHA256_checksum TEXT NOT NULL,
            FOREIGN KEY (owner_uid) REFERENCES Users(uid) ON DELETE CASCADE
        );
    """)

    # Separate table to store the users other than the owner that have been given access to a file.
    # Entries will be deleted if either the file or shared_user is deleted.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS File_Users_Shared_To (
            file_uuid TEXT NOT NULL,
            shared_user_uid INTEGER NOT NULL,
            PRIMARY KEY (file_uuid, shared_user_uid),
            FOREIGN KEY (file_uuid) REFERENCES File_Metadata(uuid) ON DELETE CASCADE,
            FOREIGN KEY (shared_user_uid) REFERENCES Users(uid) ON DELETE CASCADE
        );
    """)

    # Creates 'Audit_Log' table if it doesn't already exist
    # Action is either 'Upload' or 'Download'
    # Timestamp is stored as TEXT formatted as "yyyy-mm-dd hh:mm:ss" and is automatically logged with every new entry.
    # If a user gets deleted, associated entries will set the uid to NULL to not conflict with new or current uids.
    # Same thing if a file gets deleted.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Audit_Log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_uuid TEXT,
            owner_uid INTEGER,
            action TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_uid) REFERENCES Users(uid) ON DELETE SET NULL,
            FOREIGN KEY (file_uuid) REFERENCES File_Metadata(uuid) ON DELETE SET NULL
        );
    """)

    # Saves changes to the database file 
    conn.commit()


# -------------------------- # //////////////////////////////////////////////////////////////////////////
#     Checksum Generator     # //////////////////////////////////////////////////////////////////////////
# -------------------------- # //////////////////////////////////////////////////////////////////////////

# Seperate helper function to make SHA256 checksums for files.
# Passing the local path location of the file to this function to create a checksum when uploading to database.
# When file is downloaded, check the checksum recorded in the database with the downloaded file.

def file_checksum(path):

    # "rb" = binary read mode
    with open (path, "rb") as f:
        sha256_digest = hashlib.filedigest(f, "sha256")

    return sha256_digest.hexdigest()

# --------------------- # //////////////////////////////////////////////////////////////////////////
#     User Accounts     # //////////////////////////////////////////////////////////////////////////
# --------------------- # //////////////////////////////////////////////////////////////////////////

# Checks if the user exists already.
# Selects the UID of the user with the given username and returns it if the user exists. Otherwise returns NONE.

def check_user_exists(conn, username):

    cursor = conn.cursor()
    cursor.execute("SELECT uid FROM Users WHERE username = ?", (username,))
    row = cursor.fetchone()
    return row["uid"] if row else None


# Creates a new user account.
# Checks if the user exists already to see if username has already been taken (username has UNIQUE constraint).
# Returns UID of the new user if successful, otherwise returns NONE.

def create_user_account(conn, username, password_hash):

    cursor = conn.cursor()

    try:

        cursor.execute("INSERT INTO Users (username, password_hash) VALUES (?, ?)", (username, password_hash))
        conn.commit()
        print(f"\nCREATE USER ACCOUNT:\nUser \'{username}\' created with UID {cursor.lastrowid}.")
        return cursor.lastrowid 
    
    except sqlite3.IntegrityError:
        print(f"\nCREATE USER ACCOUNT:\nUser \'{username}\' already exists.")
        return None


# Deletes an existing user account.
# Returns TRUE if successful, otherwise returns FALSE.
# Checks if the user exists by checking if an entry is modified with DELETE.

def delete_user_account(conn, username):

    cursor = conn.cursor()

    cursor.execute("DELETE FROM Users WHERE username = ?", (username,))

    # Rowcount tracks the amount of rows modified in THIS function call. 
    # It will be more than 0 if the user is successfully deleted 
    # --- including the account itself and all files associated with it ---
    # then we can commit the changes to the database.

    if cursor.rowcount > 0:
        conn.commit()
        print(f"\nDELETE USER ACCOUNT:\nUser \'{username}\' has successfully been deleted.")
        return True
    else:
        print(f"\nDELETE USER ACCOUNT:\nUser \'{username}\' does not exist.")
        return False


# Changes a user's password.
# Checks if the account exists if an entry is modified by UPDATE.

def update_user_password(conn, username, new_password_hash):

    cursor = conn.cursor()

    cursor.execute("UPDATE Users SET password_hash = ? WHERE username = ?", (new_password_hash, username))

    # Rowcount tracks the amount of rows modified in THIS function call. 
    # It will be 1 if the user's password is successfully updated, then we can commit the changes to the database.

    if cursor.rowcount > 0:
        conn.commit()
        print(f"\nUPDATE PASSWORD:\nPassword for user \'{username}\' has been successfully updated.")
        return True
    else:
        print(f"\nUPDATE PASSWORD:\nUser \'{username}\' does not exist.")
        return False


# ------------------ # //////////////////////////////////////////////////////////////////////////
#     Audit Logs     # //////////////////////////////////////////////////////////////////////////
# ------------------ # //////////////////////////////////////////////////////////////////////////

# Adds a new entry to the audit log table tracking uploads/downloads from users.
# Should automatically mark the time the entry is created.

def create_log_entry(conn, file_uuid, owner_uid, action):

    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO Audit_Log (file_uuid, owner_uid, action) VALUES(?, ?, ?)",
        (file_uuid, owner_uid, action)
    )
    conn.commit()
    return


# ------------------------ # //////////////////////////////////////////////////////////////////////////
#     File Permissions     # //////////////////////////////////////////////////////////////////////////
# ------------------------ # //////////////////////////////////////////////////////////////////////////

# Makes sure that the file is tracked in the database.
# Selects the UUID of the file and returns it if it exists in the database. Otherwise returns NONE.

def check_file_exists(conn, uuid):

    cursor = conn.cursor()
    cursor.execute("SELECT uuid FROM File_Metadata WHERE uuid = ?", (uuid,))
    row = cursor.fetchone()
    return row["uuid"] if row else None


# Returns a list of all files that belongs to a user.

def list_user_files(conn, username):

    uid = check_user_exists(conn, username)

    if not uid:
        print(f"\nLIST USER FILES:\nUser {username} does not exist.")
        return []
    else:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM File_Metadata WHERE owner_uid = ?", (uid,))
        return cursor.fetchall()


# Returns a list of all files that have been shared to a user.

def list_files_shared_to_user(conn, username):

    uid = check_user_exists(conn, username)

    if not uid:
        print(f"\nLIST FILES SHARED TO USER:\nUser {username} does not exist.")
        return []
    else:

        cursor = conn.cursor()

        # Joins File_Users_Shared_To and File_Metadata with matching file UUID
        # and selects the files that are shared with the given user's UID.

        cursor.execute('''
            SELECT fm.* FROM File_Metadata fm
            INNER JOIN File_Users_Shared_To shared_files ON fm.uuid = shared_files.file_uuid
            WHERE shared_files.shared_user_uid = ?
        ''', (uid,))
        return cursor.fetchall()


# Function to upload a file to the database.
# File location, type, and size will be validated in main.py.
# Creates an entry in Audit_Log table when called.

def upload_file(conn, username, path):

    owner_uid = check_user_exists(conn, username)
    if not owner_uid:
        print(f"\nUPLOAD FILE:\nUser \'{username}\' does not exist.")
        return None

    # Finding the path locally on the user's machine.
    source_path = Path(path)

    if not source_path.exists():
        print(f"\nUPLOAD FILE:\nUpload failed: Local file {path} not found.")
        return None

    # Making sure that the uploaded_files directory exists first.

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # Python can generate a unique ID for file_uuid, and the Path library can check the
    # metadata on the file that we need to store in File_Metadata.

    file_uuid = str(uuid.uuid4())
    name = source_path.name
    file_size = source_path.stat().st_size
    file_type = source_path.suffix

    # Storing the file physically in the uploaded_files directory as its UUID.
    # With some help from the shutil library --> 'project_root/uploaded_files/<file_uuid>'

    stored_path = UPLOAD_DIR / file_uuid
    shutil.copy(source_path, stored_path)

    # Checksum on the file stored to 'uploaded_files'
    
    checksum = file_checksum(stored_path)

    cursor = conn.cursor()
    cursor.execute(
        '''
        INSERT INTO File_Metadata (uuid, owner_uid, name, location_path, size, type, SHA256_checksum)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (file_uuid, owner_uid, name, str(stored_path), file_size, file_type, checksum)
    )

    create_log_entry(conn, file_uuid, owner_uid, "UPLOAD")
    conn.commit()
    print(f"\nUPLOAD FILE:\nSuccessfully uploaded file \'{name}\'.\n- Assignment UUID: {file_uuid}")
    return file_uuid


# Function to delete a file from the database.

def delete_file(conn, file_uuid, file_name):

    cursor = conn.cursor()
    cursor.execute("DELETE FROM File_Metadata WHERE uuid = ?", (file_uuid,))

    # Rowcount tracks the amount of rows modified in THIS function call.
    # If a file is deleted, the number should be 1.

    if(cursor.rowcount > 0):
        conn.commit()
        print(f"\nDELETE FILE:\nFile \'{file_name}\' has been successfully deleted.")
        return True
    else:
        print(f"\nDELETE FILE:\nFile \'{file_name}\' does not exist.")
        return False


# Function to give permissions to give another user download access to a file.
# Needs to check if user and file exists first.

def share_file(conn, file_uuid, target_username):

    uid = check_user_exists(conn, target_username)
    if not uid:
        print(f"\nSHARING FILE:\nUser \'{target_username}\' does not exist.")
        return

    file = check_file_exists(conn, file_uuid)
    if not file:
        print(f"\nSHARING FILE:\nFile \'{file_uuid}\' does not exist in the database.")
        return

    cursor = conn.cursor()

    try:

        cursor.execute(
            "INSERT INTO File_Users_Shared_To (file_uuid, shared_user_uid) VALUES(?, ?)", 
            (file, uid)
        )
        conn.commit()
        print(f"\nSHARING FILE:\nFile \'{file_uuid}\' has been shared to user \'{target_username}\'.")
        return True
    
    except sqlite3.IntegrityError:
        print(f"\nSHARING FILE:\nFile \'{file_uuid}\' has already been shared with user \'{target_username}\'.")
        return False
    

# Function to take away download permissions from another user.
# Must check if the file exists first, because it may have been deleted earlier.

def unshare_file_user(conn, file_uuid, target_username):

    cursor = conn.cursor()

    if not check_file_exists(conn, file_uuid):
        print(f"\nUNSHARING FILE:\nFile {file_uuid} does not exist.")
        return False

    target_uid = check_user_exists(conn, target_username)
    
    if not target_uid:
        print(f"UNSHARING FILE:\nUser \'{target_username}\' does not exist.")
        return False

    cursor.execute(
        "DELETE FROM File_Users_Shared_To WHERE file_uuid = ? AND shared_user_uid = ?", 
        (file_uuid, target_uid)
    )

    # Rowcount tracks the amount of rows modified in THIS function call.
    # If a file is deleted, the number should be 1.

    if (cursor.rowcount > 0):
        conn.commit()
        print(f"\nUNSHARING FILE:\nFile \'{file_uuid}\' has been unshared with user \'{target_username}\'.")
        return True
    else:
        print(f"\nUNSHARING FILE:\nFile \'{file_uuid}\' is not currently shared with user \'{target_username}\'.")
        return False


# ----------------------- # //////////////////////////////////////////////////////////////////////////
#     Download Checks     # //////////////////////////////////////////////////////////////////////////
# ----------------------- # //////////////////////////////////////////////////////////////////////////

# Function to check if a user has permissions to download a file.
# The user must be the file's owner or they have to have shared access to it recorded in table 'File_Users_Shared_To'.

def check_file_download_access(conn, file_uuid, target_username):

    cursor = conn.cursor()

    target_uid = check_user_exists(conn, target_username)
    
    if not target_uid:
        print(f"\nCHECK FILE DOWNLOAD PERMISSIONS:\nUser \'{target_username}\' does not exist.")
        return False

    if not check_file_exists(conn, file_uuid):
        print(f"\nCHECK FILE DOWNLOAD PERMISSIONS:\nFile \'{file_uuid}\' does not exist.")
        return False

    # Check if the user is the owner of the file OR if it has been shared to them.
    # Left join tables and check for if there are any users who have access besides the owner that
    # matches target_uid. Otherwise, check if owner_uid matches target_uid.

    cursor.execute(
        '''
        SELECT 1 FROM File_Metadata fm
        LEFT JOIN File_Users_Shared_To shared ON fm.uuid = shared.file_uuid AND shared.shared_user_uid = ?
        WHERE fm.uuid = ? AND (fm.owner_uid = ? OR shared.shared_user_uid IS NOT NULL)
        ''', (target_uid, file_uuid, target_uid)
    )

    row = cursor.fetchone()

    if row:
        return True
    else:
        print(f"\nCHECK FILE DOWNLOAD PERMISSIONS:\nUser \'{target_username}\' does not have access to file \'{file_uuid}\'.")
        return False


# Function to download a file from the database.
# Needs to call check_file_download_access() first to see if the user has permissions to download the file.

def download_file(conn, username, file_uuid):

    if not check_file_download_access(conn, file_uuid, username):
        print(f"\nDOWNLOAD FILE:\nDownload failed. User \'{username}\' has no download access to file {file_uuid}.")
        return False

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM File_Metadata WHERE uuid = ?", (file_uuid,))
    file_row = cursor.fetchone()

    path_downloaded_from = Path(file_row["location_path"])
    if not path_downloaded_from.exists():
        print("\nDOWNLOAD FILE:\nDownload failed. Physical file missing from server storage folder.")
        return False

    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    download_path = DOWNLOAD_DIR / file_row["name"]
    shutil.copy(path_downloaded_from, download_path)

    # SHA256 verification, delete file if checksum doesn't match.

    hash_check = file_checksum(download_path)
    if hash_check != file_row["SHA256_checksum"]:
        print(f"\nDOWNLOAD FILE:\nDownloaded file hash does not match hash in database records.")
        download_path.unlink(missing_ok=True)
        return False

    user_uid = check_user_exists(username)
    create_log_entry(conn, file_uuid, user_uid, "DOWNLOAD")
    conn.commit()

    print(f"\nDOWNLOAD FILE:\nFile downloaded successfully to \'{download_path}\'")
    return True


# ----------------------- # //////////////////////////////////////////////////////////////////////////
#     Delete Database     # //////////////////////////////////////////////////////////////////////////
# ----------------------- # //////////////////////////////////////////////////////////////////////////

# If you want to delete the database later, here's a delete function.

def delete_db(db_path):
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"\nDELETE DB:\nDatabase {db_path} has been deleted successfully.")
    else:
        print(f"\nDELETE DB:\nDatabase {db_path} does not exist.")