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

from fastapi import FastAPI, HTTPException
from pathlib import Path
import sqlite3 

# Importing local files

from database_files import get_connection, db_operations
import validation
