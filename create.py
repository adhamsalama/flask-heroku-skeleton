# Creates a sqlite3 db and 2 tables for users and feedback

import sqlite3

con = sqlite3.connect('tables.db')
db = con.cursor()


with open('tables.sql') as f:
    tables = f.readlines()
    for table in tables:
        db.execute(table)
    con.commit()
    con.close()