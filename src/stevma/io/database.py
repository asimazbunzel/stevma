"""
Database module
"""

from collections import OrderedDict
import sqlite3

from .logger import logger


def create_database(database_filename: str = "", table_name: str = "", drop_table: bool = False, table_dict: OrderedDict = OrderedDict()) -> None:
    """Create table in database

    Parameters
    ----------
    database_filename : `str`
        Name of the file with the database

    table_name : `str`
        Name of the table to be created

    drop_table: `bool`
        Flag to drop (or not) `table_name` from `database_filename`

    table_dict: `dict`
        Dictionary with the information to be stored in the database
    """

    # maps between python and sqlite
    dtype_map = {
        None: "NULL",
        int: "INTEGER",
        float: "REAL",
        str: "TEXT",
        bytes: "BLOB",
        bool: "INTEGER",
    }

    # drop table
    if drop_table:

        logger.debug(f" dropping table: {table_name}")

        # create connection to db
        conn = sqlite3.connect(database_filename)

        # connect cursor
        c = conn.cursor()

        c.execute(f"DROP TABLE IF EXISTS {table_name}")

        # commit changes & close connection
        conn.commit()
        conn.close()

    logger.debug(f" creating database table: {table_name}")

    # new connection to actual table creation
    conn = sqlite3.connect(database_filename)
    c = conn.cursor()

    # first create table if it does not exist
    cmd = f"CREATE TABLE IF NOT EXISTS {table_name} ("
    for key, value in table_dict.items():

        # id key must be a primary key
        if key == "id":
            cmd += f"{key} INTEGER PRIMARY KEY, "

        # run_name must be unique. duplicates are not allowed
        elif key == "run_name":
            cmd += f"{key} {dtype_map[type(value)]} UNIQUE, "

        # the rest can be resolved by its type
        else:
            cmd += f"{key} {dtype_map[type(value)]}, "
    cmd = cmd[:-2]
    cmd += ");"

    # execute
    c.execute(cmd)

    # add INDEX in database
    cmd = f"CREATE INDEX name_index ON {table_name}(run_name);"
    c.execute(cmd)

    # commit changes & close db
    conn.commit()
    conn.close()

def insert_into_database(database_filename: str = "", table_name: str = "", table_dict: OrderedDict = OrderedDict()) -> None:
    """Insert record into database & create database if it does not exist

    Parameters
    ----------
    database_filename : `str`
        Name of the file with the database

    table_name : `str`
        Name of the table to be created

    table_dict: `dict`
        Dictionary with the information to be stored in the database
    """

    # maps between python and sqlite
    dtype_map = {
        None: "NULL",
        int: "INTEGER",
        float: "REAL",
        str: "TEXT",
        bytes: "BLOB",
        bool: "INTEGER",
    }

    conn = sqlite3.connect(database_filename)
    c = conn.cursor()

    cmd = f"INSERT INTO {table_name}"
    cmd_column_names = "("
    cmd_column_values = "("
    for key, value in table_dict.items():
        if isinstance(value, str):
            cmd_column_names += f"{key}, "
            cmd_column_values += f"'{value}', "
        else:
            cmd_column_names += f"{key}, "
            cmd_column_values += f"{value}, "
    cmd = f"{cmd} {cmd_column_names[:-2]}) VALUES {cmd_column_values[:-2]})"
    c.execute(cmd)

    conn.commit()
    conn.close()
