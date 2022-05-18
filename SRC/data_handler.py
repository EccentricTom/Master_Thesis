# import the standard libraries
import os
import pandas as pd
import sqlite3
from sqlite3 import Error
import json
import csv


# create a class to handle the data
class DataHandler:
    def __init__(self):
        basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.basedir = basedir
        self.db_path = os.path.join(basedir, 'Data', 'Contacts.db')
        if os.getcwd() == basedir:
            pass
        else:
            os.chdir(basedir)
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            print(sqlite3.version)
        except Error as e:
            print(e)

        self.con = sqlite3.connect(self.db_path)

    @staticmethod
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

    def connect(self):
        """ Connect to the SQLite database """
        if __name__ == '__main__':
            self.create_connection(self.db_path)

        con = sqlite3.connect(self.db_path)
        return con

    # check if the database is empty
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

    def create_contacts_from_csv(self, csv_file):
        """ Create a fresh table within the database
        Note: This will drop the table if it already exists"""
        con = self.connect()
        cur = con.cursor()
        cur.execute("DROP TABLE IF EXISTS Contacts")
        cur.execute("DROP TABLE IF EXISTS Updated_Contacts")
        cur.execute("CREATE TABLE Contacts (Name,Vorname,Firma,Email, Is_Valid DEFAULT 1);")
        cur.execute("CREATE TABLE Updated_Contacts (Name,Vorname,Firma,Email);")
        with open(csv_file, 'r') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for row in reader:
                cur.execute("INSERT INTO Contacts VALUES (?,?,?,?,1);", row)
        con.commit()

    def create_contacts_from_json(self, json_file):
        """ Create a fresh table within the database
        Note: This will drop the table if it already exists"""
        con = self.connect()
        cur = con.cursor()
        cur.execute("DROP TABLE IF EXISTS Contacts")
        cur.execute("DROP TABLE IF EXISTS Updated_Contacts")
        cur.execute("CREATE TABLE Contacts (Name,Vorname,Firma,Email, Is_Valid DEFAULT 1);")
        cur.execute("CREATE TABLE Updated_Contacts (Name,Vorname,Firma,Email);")
        with open(json_file, 'r') as jsonfile:
            data = json.load(jsonfile)
            for row in data:
                cur.execute("INSERT INTO Contacts VALUES (?,?,?,?,1);", row)
        con.commit()

    #upload new contacts to the database from csv file
    def upload_contacts_from_csv(self, csv_file):
        con = self.connect()
        cur = con.cursor()
        with open(csv_file, 'r') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for row in reader:
                cur.execute("INSERT INTO Updated_Contacts VALUES (?,?,?,?);", row)
        con.commit()

    #upload new contacts to the database from json file
    def upload_contacts_from_json(self, json_file):
        con = self.connect()
        cur = con.cursor()
        with open(json_file, 'r') as jsonfile:
            data = json.load(jsonfile)
            for row in data:
                cur.execute("INSERT INTO Updated_Contacts VALUES (?,?,?,?);", row)
        con.commit()

    def load_contacts(self):
        """ Load the contacts from the database """
        con = self.connect()
        df = pd.read_sql_query('SELECT * FROM Contacts', con)
        return df

    # upload dataframe into updated_contacts if it exists
    def update_contacts(self, df):
        """
        This function takes a dataframe as an argument and updates the table 'Updated_Contacts' in the database with the
        dataframe

        :param df: the dataframe you want to update
        """
        con = self.connect()
        df.to_sql('Updated_Contacts', con, if_exists='replace', index=False)
        con.commit()

    # return updated contacts
    def get_updated_contacts(self):
        """
        This function connects to the database, and then returns a dataframe of the updated contacts table
        :return: A dataframe of the updated contacts.
        """
        con = self.connect()
        df = pd.read_sql_query('SELECT * FROM Updated_Contacts', con)
        return df

    # check the number of contacts in the database
    def get_number_of_contacts(self):
        """
        This function returns the number of contacts in the database
        :return: An integer of the number of contacts in the database
        """
        con = self.connect()
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM Contacts;")
        return cur.fetchone()[0]
