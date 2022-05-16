# import the standard libraries
import os
import pandas as pd
import sqlite3
from sqlite3 import Error
import json
import csv

# create a class to handle the data
class DataHandler():
    def __init__(self):
        workdir = 'D:\HSLU_Projects\Thesis'
        if os.getcwd() != workdir:
            os.chdir(workdir)
        conn = None
        try:
            conn = sqlite3.connect(workdir + '\Data\Contacts.db')
            print(sqlite3.version)
        except Error as e:
            print(e)

        self.con = sqlite3.connect(r"D:\HSLU_projects\Thesis\Data\Contacts.db")

    def create_connection(self, db_file):
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

    def connect(self):
        """ Connect to the SQLite database """
        if __name__ == '__main__':
            self.create_connection(r"D:\HSLU_projects\Thesis\Data\Contacts.db")

        con = sqlite3.connect(r"D:\HSLU_projects\Thesis\Data\Contacts.db")
        return con

    #check if the database is empty
    def is_empty(self):
        con = self.connect()
        cur = con.cursor()
        cur.execute('SELECT * FROM Contacts')
        rows = cur.fetchall()
        if len(rows) == 0:
            return True
        else:
            return False

    def create_contacts(self):
        """ Create a fresh table within the database
        Note: This will drop the table if it already exists"""
        con = self.connect()
        cur = con.cursor()
        cur.execute("DROP TABLE IF EXISTS Contacts")
        cur.execute("DROP TABLE IF EXISTS Updated_Contacts")
        cur.execute("CREATE TABLE Contacts (Name,Vorname,Firma,Email, Is_Valid DEFAULT 1);")
        cur.execute("CREATE TABLE Updated_Contacts (Name,Vorname,Firma,Email);")

    def create_contacts_from_csv(self):
        """ Create a fresh table within the database
        Note: This will drop the table if it already exists"""
        con = self.connect()
        cur = con.cursor()
        cur.execute("DROP TABLE IF EXISTS Contacts")
        cur.execute("DROP TABLE IF EXISTS Updated_Contacts")
        cur.execute("CREATE TABLE Contacts (Name,Vorname,Firma,Email, Is_Valid DEFAULT 1);")
        cur.execute("CREATE TABLE Updated_Contacts (Name,Vorname,Firma,Email);")
        with open(r"D:\HSLU_projects\Thesis\Data\Contacts.csv", 'r') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for row in reader:
                cur.execute("INSERT INTO Contacts VALUES (?,?,?,?,1);", row)
        con.commit()

    def create_contacts_from_json(self):
        """ Create a fresh table within the database
        Note: This will drop the table if it already exists"""
        con = self.connect()
        cur = con.cursor()
        cur.execute("DROP TABLE IF EXISTS Contacts")
        cur.execute("DROP TABLE IF EXISTS Updated_Contacts")
        cur.execute("CREATE TABLE Contacts (Name,Vorname,Firma,Email, Is_Valid DEFAULT 1);")
        cur.execute("CREATE TABLE Updated_Contacts (Name,Vorname,Firma,Email);")
        with open(r"D:\HSLU_projects\Thesis\Data\Contacts.json", 'r') as jsonfile:
            data = json.load(jsonfile)
            for row in data:
                cur.execute("INSERT INTO Contacts VALUES (?,?,?,?,1);", row)
        con.commit()
    def load_contacts(self):
        """ Load the contacts from the database """
        con = self.connect()
        df = pd.read_sql_query('SELECT * FROM Contacts', con)
        return df
    #upload dataframe into updated_contacts if it exists
    def update_contacts(self, df):
        """
        This function takes a dataframe as an argument and updates the table 'Updated_Contacts' in the database with the
        dataframe

        :param df: the dataframe you want to update
        """
        con = self.connect()
        df.to_sql('Updated_Contacts', con, if_exists='replace', index=False)
        con.commit()

    # return updated contacts as json
    def get_updated_contacts(self):
        """
        It connects to the database, reads the table 'Updated_Contacts' and returns the data in JSON format
        :return: A JSON object of the updated contacts table.
        """
        con = self.connect()
        df = pd.read_sql_query('SELECT * FROM Updated_Contacts', con)
        return df.to_json(orient='records')
