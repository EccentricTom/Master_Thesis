import os
import logging
import asyncio
import numpy as np
import pandas as pd
import threading
from flask import Flask, request, jsonify

#setup the app
app = Flask(__name__)
@app.route('/')

workdir = 'D:\HSLU_Projects\Thesis'
if os.getcwd() != workdir:
    os.chdir(workdir)
else:
    pass
#setup logging in Log/app.log
logging.basicConfig(filename='Log/app.log', filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)
logging.info('Started')

from data_handler import DataHandler
from Check_contacts_bing import Check_Contacts
from Find_and_replace import ReplaceContacts


#load the data using DataHandler
handler = DataHandler()
handler.create_connection('Data/Contacts.db')
# It checks if the database is empty. If it is empty, it creates an empty DataFrame.
if not handler.is_empty():
    contacts_df = handler.load_contacts()
    logging.info('Loaded contacts from Data/Contacts.db')
else:
    contacts_df = pd.DataFrame(columns=['first_name', 'last_name', 'phone_number', 'email'])
    logging.info('Created empty contacts DataFrame')

#Continous checking of contacts in batches of 10 every 10 minutes
async def check_contacts():
    """
    It checks the contacts in the contacts_df dataframe in batches of 10 every 10 minutes
    """
    while True:
        for g, df in contacts_df.groupby(np.arange(len(contacts_df)) // 10):
            await asyncio.sleep(600)
            logging.info('Checking Contacts')
            check_contacts = Check_Contacts(df)
            contact_list = check_contacts.validation()
            if len(contact_list[contact_list['Is Valid'] == 0]) > 0:
                logging.info('Found invalid Contacts')
                replace_contacts = ReplaceContacts()
                replace_contacts.get_contacts(contact_list)
                replace_contacts.full_contact_replacement()
                logging.info('Replaced invalid Contacts')
                contacts_df.combine_first(replace_contacts.return_df())
                logging.info('Added new Contacts')
            else:
                logging.info('No invalid Contacts found')




#handler = DataHandler()
#handler.create_connection('Data/Contacts.db')
#contacts_df = handler.load_contacts()
#contacts_df = contacts_df.head(10)
#print(contacts_df)
#checker = Check_Contacts(contacts_df)
#contact_list = checker.validation()
#replacer = ReplaceContacts()
#replacer.get_contacts(contact_list)
#replacer.full_contact_replacement()
