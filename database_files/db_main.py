'''
 -----------------------
|    Database File ---  |
 -----------------------

The DB should be installed onto the file manager's device over a Local Area Network.

The DB tracks file paths on users devices (ideally in an app specific folder like 'uploaded_files')
so that users on the same LAN can share files to each other through a centralized server.
'''

import sqlite3

'''
The 'try' statement is for creating and opening the connection to the database, and
'with' should automatically close the connection after it is finished.

- If the database has not been established yet, then the code should create one named 'filesharing.db'
  and create the tables 'Users', 'File_Metadata', and 'Audit_Log' as we have defined in the schema.
- An additional table 'File_Users_Shared_To' is a separate table made to store the UIDs of users
  that the owner has shared access to a specific files to.
'''

# Path on device, can change it here :3
database_path = "filesharing.db"

try:
    with sqlite3.connect(database_path) as conn:
        print(f"Opened SQLite database with version {sqlite3.sqlite_version} successfully.")

        # Creates a cursor to connect the database to Python,
        # And turning on foreign keys just in case it was off by default so that the tables can work.

        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")

        # Creates 'Users' table if it doesn't already exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Users (
                uid INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
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

except:
    print("Failed to open database: ", sqlite3.OperationalError)

