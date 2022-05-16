import pandas as pd
import os
import json

pd.set_option("display.max_rows", None)
from tqdm import tqdm
from tqdm.notebook import tqdm as notebook_tqdm
import time

os.environ['WDM_LOG'] = '0'
os.environ['WDM_LOG_LEVEL'] = '0'

import spacy
# Importing the unidecode module.
import unidecode

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common import exceptions
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup

# ------------ stopword collection----------#
en = spacy.load('en_core_web_sm')
stopwords_en = en.Defaults.stop_words
de = spacy.load('de_core_news_lg')
stopwords_de = de.Defaults.stop_words
stopwords = stopwords_en.union(stopwords_de)

# ------------ load NER model----------#
ner = spacy.load('en_core_web_lg')


# -----------------------------------------------------------------------------------------------------------------------------------#

# It's a class that contains functions to replace the contacts in the
# dataframe with the contacts from the LinkedIn website.
# This class is used to replace the contacts in a given contact group with the contacts in a given CSV file.
class ReplaceContacts:
    def __init__(self):
        """
        The function initializes the webdriver, sets the options for the webdriver, loads the acronyms and umlaut
        dictionaries, loads the NER model and sets the dataframe to None
        """
        self.service = Service(executable_path=ChromeDriverManager().install())
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--log-level = 3")
        workdir = 'D:\HSLU_Projects\Thesis'
        if os.getcwd() != workdir:
            os.chdir(workdir)
        else:
            pass
        f = open(r'Data/common_acronyms.json')
        self.acronyms = json.load(f)
        f.close()
        f = open('Data/umlautDictionary.json')
        umlautDictionary = json.load(f)
        f.close()
        self.umap = {ord(key): val for key, val in umlautDictionary.items()}
        self.ner_model = spacy.load('en_core_web_lg')
        # self.df will be loaded with the get_contacts function
        self.df = None

    # Load the contact dataframe from check_contacts.py into here
    def get_contacts(self, df):
        """
        *|CURSOR_MARCADOR|*

        :param df: The dataframe that contains the data
        """
        self.df = df

    # function to clean up text
    def clean_text(self, page):
        """
        It takes a page of text, strips it of HTML tags, splits it into a list of words, removes stopwords, and returns a
        string of the remaining words

        :param page: the HTML page to be cleaned
        :return: A string of the cleaned text.
        """
        soup = BeautifulSoup(page, 'html.parser')
        cleanup = soup.get_text().strip()
        jumble = cleanup.split()
        cleaned = ' '.join(jumble).strip()
        finish = []
        for word in cleaned.split():
            if word not in stopwords:
                finish.append(word)
        final = ' '.join(finish)
        return final

    # function to find the contact name
    def contact_person(self, page):
        """
        It takes a page of text, tags it with the NER model, and returns the first person it finds

        :param page: the text of the page
        :return: The name of the contact person.
        """
        tagged_page = self.ner_model(page)
        persons = []
        for ent in tagged_page.ents:
            if ent.label_ == 'PERSON':
                persons.append(ent.text)
        person = persons[0]
        if ' - ' in person:
            person = person.split(' - ')[0]
        return person

    # function to find the correct email address format
    def create_email_rules(self, random_slice):
        """
        This function takes a random slice of the dataframe, and then creates a list of email formats based on the first and
        last name of the person in the slice.

        The function then checks if the email format in the slice matches any of the email formats in the list. If it does,
        it returns the expression that created the email format.

        If it doesn't, it returns False.

        :param random_slice: a slice of the dataframe that contains the first name, last name, and email of the person you
        want to create a rule for
        :return: A string that is the expression that was used to create the email.
        """
        umap = self.umap
        first_name = random_slice['Vorname'].lower().translate(umap)
        first_name = unidecode.unidecode(first_name)
        last_name = random_slice['Name'].lower().translate(umap)
        last_name = unidecode.unidecode(last_name)
        last_name = last_name.replace("'", "")
        email = random_slice['Email']
        print(email)
        domain = random_slice['Email'].split('@')[1]
        if len(last_name.split(' ')) > 1:
            print(last_name.split(' ')[0], last_name.split(' ')[1])
            if last_name.split(' ')[0] in email or last_name.split(' ')[1] in email:
                print("Email format is correct")
                return True
            else:
                print("Email format is incorrect")
                return False
        if first_name not in email or last_name not in email:
            print("This is a specific email format, double-checking...")
            if 'mail' in email or 'info' in email:
                print("this is the genereric info email, use this")
                return email
        format1 = first_name[0] + last_name + '@' + domain
        expression1 = "first_name[0] + last_name + '@' + domain"
        format2 = first_name + last_name[0] + '@' + domain
        expression2 = "first_name + last_name[0] + '@' + domain"
        format_3 = first_name + last_name + '@' + domain
        expression_3 = "first_name + last_name + '@' + domain"
        format_4 = first_name + '.' + last_name + '@' + domain
        expression_4 = "first_name + '.' + last_name + '@' + domain"
        format_5 = first_name + '_' + last_name + '@' + domain
        expression_5 = "first_name + '_' + last_name + '@' + domain"
        format_6 = first_name + '-' + last_name + '@' + domain
        expression_6 = "first_name + '-' + last_name + '@' + domain"
        format_7 = last_name + '.' + first_name + '@' + domain
        expression_7 = "last_name + '.' + first_name + '@' + domain"
        format_8 = last_name + '_' + first_name + '@' + domain
        expression_8 = "last_name + '_' + first_name + '@' + domain"
        format_9 = last_name + '-' + first_name + '@' + domain
        expression_9 = "last_name + '-' + first_name + '@' + domain"
        format_10 = last_name.split(' ')[0] + first_name[0] + '@' + domain
        expression_10 = "last_name.split(' ')[0] + first_name[0] + '@' + domain"
        format_11 = last_name.split(' ')[0] + first_name + '@' + domain
        expression_11 = "last_name.split(' ')[0] + first_name + '@' + domain"
        format_12 = last_name.split(' ')[0][0] + first_name + '@' + domain
        expression_12 = "last_name.split(' ')[0][0] + first_name + '@' + domain"
        format_13 = first_name + '.' + last_name.split(' ')[0] + '@' + domain
        expression_13 = "first_name + '.' + last_name.split(' ')[0] + '@' + domain"
        format_14 = first_name + '_' + last_name.split(' ')[0] + '@' + domain
        expression_14 = "first_name + '_' + last_name.split(' ')[0] + '@' + domain"
        format_15 = first_name + '-' + last_name.split(' ')[0] + '@' + domain
        expression_15 = "first_name + '-' + last_name.split(' ')[0] + '@' + domain"
        format_16 = last_name + first_name + '@' + domain
        expression_16 = "last_name + first_name + '@' + domain"
        format_17 = first_name[0] + '.' + last_name + '@' + domain
        expression_17 = "first_name[0] + '.' + last_name + '@' + domain"
        format_18 = first_name + last_name.split('-')[0] + '@' + domain
        expression_18 = "first_name + last_name.split('-')[0] + '@' + domain"
        format_19 = first_name + last_name.split('_')[0] + '@' + domain
        expression_19 = "first_name + last_name.split('_')[0] + '@' + domain"
        format_20 = first_name + "." + last_name.split('-')[0] + '@' + domain
        expression_20 = "first_name + '.' + last_name.split('-')[0] + '@' + domain"
        format_21 = first_name + "_" + last_name.split('-')[0] + '@' + domain
        expression_21 = "first_name + '_' + last_name.split('-')[0] + '@' + domain"
        format_22 = last_name + first_name[0] + '@' + domain
        expression_22 = "last_name + first_name[0] + '@' + domain"
        format_23 = last_name + "." + first_name[0] + '@' + domain
        expression_23 = "last_name + '.' + first_name[0] + '@' + domain"
        format_24 = last_name + "_" + first_name[0] + '@' + domain
        expression_24 = "last_name + '_' + first_name[0] + '@' + domain"
        format_25 = last_name + first_name + '@' + domain
        expression_25 = "last_name + first_name + '@' + domain"
        format_26 = first_name[0] + '.' + last_name[0] + '@' + domain
        expression_26 = "first_name[0] + '.' + last_name[0] + '@' + domain"
        format_27 = first_name[0] + '_' + last_name[0] + '@' + domain
        expression_27 = "first_name[0] + '_' + last_name[0] + '@' + domain"
        format_28 = last_name[0] + first_name[0] + '@' + domain
        expression_28 = "last_name[0] + first_name[0] + '@' + domain"
        format_29 = last_name[0] + '.' + first_name[0] + '@' + domain
        expression_29 = "last_name[0] + '.' + first_name[0] + '@' + domain"
        format_30 = last_name[0] + '_' + first_name[0] + '@' + domain
        expression_30 = "last_name[0] + '_' + first_name[0] + '@' + domain"
        format_31 = first_name[0] + last_name[0] + '@' + domain
        expression_31 = "first_name[0] +  last_name[0] + '@' + domain"

        format_list = [format1, format2, format_3, format_4, format_5, format_6, format_7, format_8, format_9,
                       format_10, format_11, format_12, format_13, format_14, format_15, format_16, format_17,
                       format_18, format_19, format_20, format_21, format_22, format_23, format_24, format_25,
                       format_26, format_27, format_28, format_29, format_30, format_31]
        expression_list = [expression1, expression2, expression_3, expression_4, expression_5, expression_6,
                           expression_7, expression_8, expression_9, expression_10, expression_11, expression_12,
                           expression_13, expression_14, expression_15, expression_16, expression_17, expression_18,
                           expression_19, expression_20, expression_21, expression_22, expression_23, expression_24,
                           expression_25, expression_26, expression_27, expression_28, expression_29, expression_30,
                           expression_31]
        for format in format_list:
            if format == email:
                print(expression_list[format_list.index(format)])
                return expression_list[format_list.index(format)]

    # function to find new contact - currently defaulting to head of communications
    def find_new_contact(self, random_slice):
        """
        It takes a random slice of the dataframe, searches for the company name and the job title in Google, and returns the
        text of the first page of the search results

        :param random_slice: a dictionary with the following keys:
        :return: The page is being returned.
        """
        driver = webdriver.Chrome(service=self.service, options=self.chrome_options)
        driver.implicitly_wait(25)
        driver.get("https://www.google.com/")
        try:
            WebDriverWait(driver, 5).until(
                expected_conditions.element_to_be_clickable((By.XPATH,
                                                             "/html/body/div[2]/div[2]/div[3]/span/div/div/div/div["
                                                             "3]/button[2]"))).click()
        except:
            pass
        m = driver.find_element(by=By.NAME, value='q')
        m.send_keys(random_slice['Firma'] + " Head of Communication Switzerland")
        m.send_keys(Keys.RETURN)

        first_page = page = driver.find_element(By.TAG_NAME, "body").text
        if "featured snippet" in first_page:
            print("Featured snippet found, extract team from here")
            try:
                WebDriverWait(driver, 5).until(expected_conditions.element_to_be_clickable((By.XPATH,
                                                                                            '//*[@id="rso"]/div['
                                                                                            '1]/block-component/div'
                                                                                            '/div['
                                                                                            '1]/div/div/div/div/div['
                                                                                            '1]/div/div/div/div/div'
                                                                                            '/div[2]/div/div/div['
                                                                                            '1]'))).click()
                page = driver.find_element(By.TAG_NAME, "body").text
            except:
                print("Can't find the element")
                pass
        else:
            print("not found, going to first link")

            try:
                check_for_linkedin = driver.find_element(By.XPATH, '//*[@id="rso"]/div[1]').text
                print(check_for_linkedin)
                if "https://ch.linkedin.com" in check_for_linkedin:
                    print("LinkedIn found, extract info from here")
                    page = check_for_linkedin
                else:
                    print("LinkedIn not found, going to first link")
                    WebDriverWait(driver, 5).until(
                        expected_conditions.element_to_be_clickable((By.XPATH,
                                                                     '//*[@id="rso"]/div[1]/div/div[1]/div/a/h3'))).click()
                    time.sleep(5)
                    if driver.findElement(By.XPATH, '/html/body/div[4]/div/div/div[2]/div[1]/button').size() != 0:
                        WebDriverWait(driver, 5).until(
                            expected_conditions.element_to_be_clickable((By.XPATH,
                                                                         '/html/body/div[4]/div/div/div[2]/div['
                                                                         '1]/button'))).click()
                        page = driver.find_element(By.TAG_NAME, "body").text
                    else:
                        page = driver.find_element(By.TAG_NAME, "body").text
            except:
                print("Can't find the element")
                pass

        driver.close()
        return page

    # function to build email from found contact
    def create_email(self, random_slice, person, email_format):
        """
        It takes a random slice of the dataframe, a person's name, and an email format, and returns an email address

        :param random_slice: a dictionary of the random slice of data
        :param person: The name of the person you want to create an email for
        :param email_format: This is a string that contains the format of the email address
        :return: The email address of the person.
        """
        first_name = person.split(" ")[0]
        if len(person.split(" ")) == 2:
            last_name = person.split(" ")[1]
        else:
            list_person = person.split(" ")
            extreneous = list_person.pop(0)
            last_name = ' '.join(list_person)
            del(extreneous)
        domain = random_slice['Email'].split('@')[1]
        email = eval(email_format)
        return email

    # function to find and replace invalid contact
    def find_and_replace(self, df):
        """
        This function takes a dataframe and returns a dataframe with the new contact information

        :param df: the dataframe that contains the company name and the url to the company's website
        :return: Email, Vorname, Name, Firma
        """
        print("checking for new contact for {}".format(df['Firma']))
        page = self.find_new_contact(df)
        cleaned_page = self.clean_text(page)
        person = self.contact_person(cleaned_page)
        email_format = self.create_email_rules(df)
        Email = self.create_email(df, person, email_format)
        Vorname = person.split(" ")[0]
        if len(person.split(" ")) == 2:
            Name = person.split(" ")[1]
        else:
            person_list = person.split(" ")
            extreneous = person_list.pop(0)
            del(extreneous)
            Name = ' '.join(person_list)
        Firma = df['Firma']
        print("the new contact for {} is {} {} with email {}".format(Firma, Vorname, Name, Email))
        return Name, Vorname, Email, Firma

    # function to iterate over all wrong contacts and replace with new contact
    def full_contact_replacement(self, df=None, debug=False):
        """
        It takes a dataframe with wrong contacts and replaces them with the correct ones

        :param df: the dataframe to be corrected
        """
        if df is not None:
            self.get_contacts(df)
        wrong_contacts = self.df[self.df['Is_Valid'] == 0]
        corrected_contacts = wrong_contacts.copy()
        print(wrong_contacts['Email'])
        for idx, row in wrong_contacts.iterrows():
            Name, Vorname, Email, Firma = self.find_and_replace(df=row)
            corrected_contacts.loc[idx, 'Name'] = Name
            corrected_contacts.loc[idx, 'Vorname'] = Vorname
            corrected_contacts.loc[idx, 'Email'] = Email
            corrected_contacts.loc[idx, 'Firma'] = Firma
            corrected_contacts.loc[idx, 'Is_Valid'] = 1
        print("{} wrong contacts replaced".format(len(corrected_contacts)))
        if debug:
            confirmation = input("Do you want to save the new dataframe? (y/n/debug)")
            if confirmation == 'y':
                self.df = self.df.combine_first(corrected_contacts)
            elif confirmation == 'debug':
                print("compare the two dataframes")
                print(self.df)
                print('-' * 50)
                print(corrected_contacts)
                pass
            else:
                print("Contact replacement cancelled")
        else:
            self.df = self.df.combine_first(corrected_contacts)

    def return_df(self):
        """
        The function returns the dataframe with the corrected contacts
        :return: The dataframe is being returned.
        """
        return self.df
