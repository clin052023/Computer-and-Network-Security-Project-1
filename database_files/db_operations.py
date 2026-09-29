'''
 ---------------------------------
|    Database Functions File ---  |
 ---------------------------------

 Separate files for database operations to call while the app is running.
'''

import sqlite3
import os


# Function to give permissions to give another user download access to a file.

def share_file():
    return


# Function to take away download permissions from another user.

def unshare_file():
    return


# Function to check if a user has permissions to download a file.

def check_file_download_access():
    return


# If you want to delete the database later, here's a delete function.

def delete_function(db_path):
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Database {db_path} has been deleted successfully.")
    else:
        print(f"Database {db_path} does not exist.")