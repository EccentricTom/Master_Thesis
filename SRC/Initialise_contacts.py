import sqlite3
from sqlite3 import Error
import csv
import os

workdir = 'D:\HSLU_Projects\Thesis'
if os.getcwd() != workdir:
    os.chdir(workdir)
    print(f"Working Directory is now {os.getcwd()}")
else:
    print(f"Working Directory is already set to {os.getcwd()}")

def create_connection(db_file):
    """ create a database connection to a SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(sqlite3.version)
    except Error as e:
        print(e)
    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    create_connection(r"D:\HSLU_projects\Thesis\Data\Contacts.db")

con = sqlite3.connect(r"D:\HSLU_projects\Thesis\Data\Contacts.db")
cur = con.cursor()

#cur.execute("SELECT name FROM Contacts;")
print("Table found")
cur.execute("DROP TABLE IF EXISTS Contacts")

cur.execute("CREATE TABLE Contacts (Name,Vorname,Firma,Email, Is_Valid DEFAULT 1);")
cur.execute("DROP TABLE IF EXISTS Updated_Contacts")
cur.execute("CREATE TABLE Updated_Contacts (Name,Vorname,Firma,Email);")
with open("Data/training_data.csv", 'r', encoding='utf-8') as data:
    dr = csv.DictReader(data)
    to_db = [(i['Name'], i['Vorname'], i['Firma'], i['Email']) for i in dr]
cur.executemany("INSERT INTO Contacts (Name,Vorname,Firma,Email) VALUES (?,?,?,?);", to_db)
con.commit()
con.close()