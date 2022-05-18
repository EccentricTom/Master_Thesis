import os
import logging
import asyncio
import numpy as np
import pandas as pd
import threading
from flask import Flask, request, jsonify

basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if os.getcwd() == basedir:
    pass
else:
    os.chdir(basedir)

from data_handler import DataHandler
from Check_contacts_bing import Check_Contacts
from Find_and_replace import ReplaceContacts

handler = DataHandler()
handler.create_connection('Data/Contacts.db')
contacts_df = handler.load_contacts()
contacts_df = contacts_df.head(10)
print(contacts_df)
checker = Check_Contacts(contacts_df)
contact_list = checker.validation()
replacer = ReplaceContacts()
replacer.get_contacts(contact_list)
replacer.full_contact_replacement()
