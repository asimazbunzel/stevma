"""
Database module
"""

from collections import OrderedDict
import sqlite3


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

    # first create table if it does not exist
    cmd = f"CREATE TABLE IF NOT EXISTS {table_name} ("
    for key, value in table_dict.items():
        if value is None:
            cmd += f"{key} REAL, "
        else:
            cmd += f"{key} {dtype_map[type(value)]}, "
    cmd = cmd[:-2]
    cmd += ");"

    c.execute(cmd)

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
