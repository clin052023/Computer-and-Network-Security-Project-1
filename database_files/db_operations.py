'''
 ----------------------------------
|         db_operations.py         |
|               ---                |
|    Database Operations File ---  |
 ----------------------------------

 Separate file for database operations to call while the app is running.
'''

import sqlite3
import os


# ----------------------- # //////////////////////////////////////////////////////////////////////////
#     Create Database     # //////////////////////////////////////////////////////////////////////////
# ----------------------- # //////////////////////////////////////////////////////////////////////////

# Function to create the database and initializes tables if they don't exist yet.
# The database should be named "filesharing.db" and have the tables 'Users', 'File_Metadata', and 'Audit_Log' 
# as we have defined in the schema.
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
            owner_uid INTEGER,
            name TEXT NOT NULL,
            location_path TEXT,
            size INTEGER NOT NULL,
            type TEXT NOT NULL,
            SHA256_checksum TEXT,
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
    # Timestamp is stored as TEXT formatted as "yyyy-mm-dd hh:mm:ss"
    # If a user gets deleted, associated entries will set the uid to NULL to not conflict with new or current uids.
    # Same thing if a file gets deleted.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Audit_Log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_uuid TEXT,
            owner_uid INTEGER,
            action TEXT,
            timestamp TEXT,
            FOREIGN KEY (owner_uid) REFERENCES Users(uid) ON DELETE SET NULL,
            FOREIGN KEY (file_uuid) REFERENCES File_Metadata(uuid) ON DELETE SET NULL
        );
    """)

    # Saves changes to the database file 
    conn.commit()


# --------------------- # //////////////////////////////////////////////////////////////////////////
#     User Accounts     # //////////////////////////////////////////////////////////////////////////
# --------------------- # //////////////////////////////////////////////////////////////////////////

# Checks if the user exists already.
# Selects the UID of the user with the given username and returns TRUE if the user exists.

def check_user_exists(conn, username):

    cursor = conn.cursor()
    cursor.execute("SELECT uid FROM Users WHERE username = ?", (username,))
    return cursor.fetchone() is not None


# Creates a new user account.
# Checks if the user exists already to see if username has already been taken (username has UNIQUE constraint).
# Returns UID of the new user if successful, otherwise returns None.

def create_user_account(conn, username, password_hash):

    cursor = conn.cursor()

    try:

        cursor.execute("INSERT INTO Users (username, password_hash) VALUES (?, ?)", (username, password_hash))
        conn.commit()
        print(f"\nUser \'{username}\' created with UID {cursor.lastrowid}.")
        return cursor.lastrowid 
    
    except sqlite3.IntegrityError:
        print(f"\nUser \'{username}\' already exists.")
        return None


# Deletes an existing user account.
# Returns TRUE if successful, otherwise returns FALSE.
# Checks if the user exists first (username has UNIQUE constraint in database).

def delete_user_account(conn, username):

    cursor = conn.cursor()

    cursor.execute("DELETE FROM Users WHERE username = ?", (username,))

    # Rowcount tracks the amount of rows modified in THIS function call. 
    # It will be more than 0 if the user is successfully deleted 
    # --- including the account itself and all files associated with it ---
    # then we can commit the changes to the database.

    if cursor.rowcount > 0:
        conn.commit()
        print(f"\nUser \'{username}\' has successfully been deleted.")
        return True
    else:
        print(f"\nUser \'{username}\' does not exist.")
        return False


# Changes a user's password.
# Checks if the account exists first.

def update_user_password(conn, username, new_password_hash):

    cursor = conn.cursor()

    cursor.execute("UPDATE Users SET password_hash = ? WHERE username = ?", (new_password_hash, username))

    # Rowcount tracks the amount of rows modified in THIS function call. 
    # It will be 1 if the user's password is successfully updated, then we can commit the changes to the database.

    if cursor.rowcount > 0:
        conn.commit()
        print(f"\nPassword for user \'{username}\' has been successfully updated.")
        return True
    else:
        print(f"\nUser \'{username}\' does not exist.")
        return False


# ------------------------ # //////////////////////////////////////////////////////////////////////////
#     File Permissions     # //////////////////////////////////////////////////////////////////////////
# ------------------------ # //////////////////////////////////////////////////////////////////////////

# Makes sure that the file is tracked in the database.
# Selects the UUID of the file and returns TRUE if it exists in the database.

def check_file_exists(conn, uuid):

    cursor = conn.cursor()
    cursor.execute("SELECT uuid FROM File_Metadata WHERE uuid = ?", (uuid,))
    return cursor.fetchone() is not None


# Returns a list of all files that belongs to a user.

def list_user_files(conn):

    cursor = conn.cursor()
    return


# Returns a list of all files that have been shared to a user.

def list_files_shared_to_user(conn):

    cursor = conn.cursor()
    return


# Function to upload a file to the database.

def upload_file(conn):

    cursor = conn.cursor()
    return


# Function to delete a file from the database.

def delete_file(conn):

    cursor = conn.cursor()
    return


# Function to give permissions to give another user download access to a file.
# Needs to check if user exists first.

def share_file(conn):

    cursor = conn.cursor()
    return


# Function to take away download permissions from another user.
# Must check if the file exists first, because it may have been deleted earlier.

def unshare_file_user(conn):

    cursor = conn.cursor()
    return


# ----------------------- # //////////////////////////////////////////////////////////////////////////
#     Download Checks     # //////////////////////////////////////////////////////////////////////////
# ----------------------- # //////////////////////////////////////////////////////////////////////////

# Function to check if a user has permissions to download a file.
# Checks if the file exists to begin with first, then checks user permissions.

def check_file_download_access(conn):

    cursor = conn.cursor()
    return


# Function to download a file from the database.
# Needs to call check_file_download_access() first to see if the user has permissions to download the file.

def download_file(conn):

    cursor = conn.cursor()
    return


# ------------------ # //////////////////////////////////////////////////////////////////////////
#     Audit Logs     # //////////////////////////////////////////////////////////////////////////
# ------------------ # //////////////////////////////////////////////////////////////////////////

# Adds a new entry to the audit log table tracking uploads/downloads from users.

def create_log_entry(conn):

    cursor = conn.cursor()
    return


# ----------------------- # //////////////////////////////////////////////////////////////////////////
#     Delete Database     # //////////////////////////////////////////////////////////////////////////
# ----------------------- # //////////////////////////////////////////////////////////////////////////

# If you want to delete the database later, here's a delete function.

def delete_db(db_path):
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Database {db_path} has been deleted successfully.")
    else:
        print(f"Database {db_path} does not exist.")