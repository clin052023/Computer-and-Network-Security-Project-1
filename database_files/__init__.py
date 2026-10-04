'''
 -----------------------------
|         __init__.py         |
 -----------------------------

 For main.py so that the entire directory can be imported.
'''

from database_files.db_main import get_connection
from database_files import db_operations as db_ops