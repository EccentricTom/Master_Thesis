import os
import logging
import time
import numpy as np
import pandas as pd
from datetime import datetime
from flask import Flask, request, jsonify
from threading import Thread

# set up the app
app = Flask("Contact_Checker")
basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if os.getcwd() == basedir:
    pass
else:
    os.chdir(basedir)

# setup the logger
now = datetime.now()
log_file_name = 'Log/app_started_' + now.strftime("%Y-%m-%d_at_%H-%M-%S") + '.log'
logger = logging.getLogger(log_file_name)
logging.basicConfig(filename=log_file_name, filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.INFO)

from data_handler import DataHandler
from Check_contacts_bing import Check_Contacts
from Find_and_replace import ReplaceContacts

logging.info('Loaded functions')


# Continous checking of contacts in batches of 10 every 10 minutes
def check_contacts(contact_df):
    """
    It checks the contacts in the contacts_df dataframe in batches of 10 every 10 minutes
    """
    while True:
        for g, df in contact_df.groupby(np.arange(len(contact_df)) // 10):
            logging.info('Checking Contacts')
            check_contacts = Check_Contacts(df, logging=logging)
            contact_list = check_contacts.validation()
            if len(contact_list[contact_list['Is_Valid'] == 0]) > 0:
                logging.info('Found invalid Contacts')
                replace_contacts = ReplaceContacts(logging=logging)
                replace_contacts.get_contacts(contact_list)
                replace_contacts.full_contact_replacement()
                logging.info('Replaced invalid Contacts')
                contact_df.update(replace_contacts.return_df())
                logging.info('Added new Contacts')
            else:
                logging.info('No invalid Contacts found')
            time.sleep(600)
        if len(contact_df[contact_df['Is Valid'] == 0]) == 0:
            logging.info(
                f'There are still {len(contact_df[contact_df["Is Valid"] == 0]) == 0} contacts out of date that '
                f'could not be replaced')
        handler.update_contacts(contact_df)
        logging.info("Finished checking Contacts, starting again...")


# Load json file with contacts via API
@app.route('/update_contacts_json', methods=['PUT'])
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
@app.route('/update_contacts_csv', methods=['PUT'])
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
@app.route('/contacts_json_replace', methods=['POST'])
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
@app.route('/contacts_csv_replace', methods=['POST'])
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


# retrieve updated contact list
@app.route('/request_updated_contacts', methods=['GET'])
def get_contacts_updated():
    """
    It returns the contacts_df dataframe with the updated contacts
    :return: A json object with the updated contacts
    """
    logging.info('Received GET request')
    return jsonify((handler.get_updated_contacts().to_json(orient='records')))


# start the app
if __name__ == '__main__':
    # load the data using DataHandler
    logging.info('Loading data')
    handler = DataHandler()
    handler.create_connection('Data/Contacts.db')
    # It checks if the database is empty. If it is empty, it creates an empty DataFrame.
    if not handler.is_empty():
        contacts_df = handler.load_contacts()
        logging.info('Loaded contacts from Data/Contacts.db')
    else:
        contacts_df = pd.DataFrame(columns=['first_name', 'last_name', 'phone_number', 'email'])
        logging.info('Created empty contacts DataFrame')
    # setup the thread for checking contacts periodically
    logging.info("Starting contacts checking thread")
    contact_checker = Thread(target=check_contacts, args=(contacts_df,))
    contact_checker.daemon = True
    contact_checker.start()

    # start the app
    logging.info('Starting app')
    app.run(threaded=True, debug=True)  # fill in later
