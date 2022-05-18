import os
import logging
import asyncio
import numpy as np
import pandas as pd
from datetime import datetime
from flask import Flask, request, jsonify

# set up the app
app = Flask(__name__)
basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if os.getcwd() == basedir:
    pass
else:
    os.chdir(basedir)

# setup the logger
now = datetime.now()
log_file_name = 'logs/app_started_' + now.strftime("%Y-%m-%d") + '.log'
logging.basicConfig(filename=log_file_name, filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

from data_handler import DataHandler
from Check_contacts_bing import Check_Contacts
from Find_and_replace import ReplaceContacts

logging.info('Loaded functions')


# Continous checking of contacts in batches of 10 every 10 minutes
async def check_contacts():
    """
    It checks the contacts in the contacts_df dataframe in batches of 10 every 10 minutes
    """
    while True:
        for g, df in contacts_df.groupby(np.arange(len(contacts_df)) // 10):
            await asyncio.sleep(600)
            logging.info('Checking Contacts')
            check_contacts = Check_Contacts(df, logging=logging)
            contact_list = check_contacts.validation()
            if len(contact_list[contact_list['Is Valid'] == 0]) > 0:
                logging.info('Found invalid Contacts')
                replace_contacts = ReplaceContacts()
                replace_contacts.get_contacts(contact_list)
                replace_contacts.full_contact_replacement()
                logging.info('Replaced invalid Contacts')
                contacts_df.update(replace_contacts.return_df())
                logging.info('Added new Contacts')
            else:
                logging.info('No invalid Contacts found')
        if len(contacts_df[contacts_df['Is Valid'] == 0]) == 0:
            logging.info(
                f'There are still {len(contacts_df[contacts_df["Is Valid"] == 0]) == 0} contacts out of date that '
                f'could not be replaced')
        handler.update_contacts(contacts_df)
        logging.info("Finished checking Contacts, starting again...")


# run asyncio loop continuously while app is running
async def main():
    """
    It runs the check_contacts function every 10 minutes
    """
    while True:
        await check_contacts()


# start the app
if __name__ == '__main__':
    # start the app
    logging.info('Starting app')
    app.run(host="1234")  # fill in later

logging.info('Started')

# load the data using DataHandler
handler = DataHandler()
handler.create_connection('Data/Contacts.db')
# It checks if the database is empty. If it is empty, it creates an empty DataFrame.
if not handler.is_empty():
    contacts_df = handler.load_contacts()
    logging.info('Loaded contacts from Data/Contacts.db')
else:
    contacts_df = pd.DataFrame(columns=['first_name', 'last_name', 'phone_number', 'email'])
    logging.info('Created empty contacts DataFrame')

# start the asyncio loop
loop = asyncio.get_event_loop()
loop.ensure_future(main())
logging.info('Check Contact Loop Started')


# Load json file with contacts via API
@app.route('/api/contacts_json', methods=['PUT'])
def put_contacts_json():
    """
    It adds the contacts from the json file to the contacts_df dataframe
    """
    logging.info('Received PUT request')
    data = request.get_json()
    logging.info('Received data')
    count_before = handler.get_number_of_contacts()
    handler.upload_contacts_from_json(data['contacts'])
    count_after = handler.get_number_of_contacts()
    logging.info('Added contacts to the Contacts database')
    return f"Added {count_after - count_before} contacts to the Contacts database"


# Load csv file with contacts via API
@app.route('/api/contacts_csv', methods=['PUT'])
def put_contacts_csv():
    """
    It adds the contacts from the csv file to the contacts_df dataframe
    """
    logging.info('Received PUT request')
    data = request.get_json()
    logging.info('Received data')
    count_before = handler.get_number_of_contacts()
    handler.upload_contacts_from_csv(data['contacts'])
    count_after = handler.get_number_of_contacts()
    logging.info('Added contacts to the Contacts database')
    return f"Added {count_after - count_before} contacts to the Contacts database"


# Load json file with contacts via API and replace existing contacts
@app.route('/api/contacts_json_replace', methods=['POST'])
def post_contacts_json():
    """
    It receives a JSON object, wipes the contacts table, and adds the new contacts to the database
    :return: A string that says "Existing contacts deleted, added {count_after} contacts to the Contacts database"
    """
    logging.info('Received POST request')
    data = request.get_json()
    logging.info('Received data')
    handler.create_contacts_from_json(data['contacts'])
    logging.info('Wiped contacts table and added new contacts')
    count_after = handler.get_number_of_contacts()
    return f"Existing contacts deleted, added {count_after} contacts to the Contacts database"


# Load csv file with contacts via API and replace existing contacts
@app.route('/api/contacts_csv_replace', methods=['POST'])
def post_contacts_csv():
    """
    It receives a CSV object, wipes the contacts table, and adds the new contacts to the database
    :return: A string that says "Existing contacts deleted, added {count_after} contacts to the Contacts database"
    """
    logging.info('Received POST request')
    data = request.get_json()
    logging.info('Received data')
    handler.create_contacts_from_csv(data['contacts'])
    logging.info('Wiped contacts table and added new contacts')
    count_after = handler.get_number_of_contacts()
    return f"Existing contacts deleted, added {count_after} contacts to the Contacts database"


#retrieve updated contact list
@app.route('/api/contacts_updated', methods=['GET'])
def get_contacts_updated():
    """
    It returns the contacts_df dataframe with the updated contacts
    :return: A json object with the updated contacts
    """
    logging.info('Received GET request')
    return jsonify((handler.get_updated_contacts().to_json(orient='records')))
