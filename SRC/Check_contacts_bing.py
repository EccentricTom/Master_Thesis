# Python Base Packages
import pandas as pd
import time
import os
import json
import sqlite3

# Progress bar
from tqdm import tqdm

# Fuzzy string matching
from fuzzysearch import find_near_matches

# NLP
import spacy

# Web Scraping
from selenium import webdriver
from selenium.common import exceptions
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from fake_useragent import UserAgent

# ----------------- Formatting --------------------------------- #
pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
os.environ['WDM_LOG'] = '0'
os.environ['WDM_LOG_LEVEL'] = '0'

# ------------ stopwords collection----------#
en = spacy.load('en_core_web_sm')
stopwords_en = en.Defaults.stop_words
de = spacy.load('de_core_news_lg')
stopwords_de = de.Defaults.stop_words
stopwords_full = stopwords_en.union(stopwords_de)


# ---------------------------------------------------------------------------------------------------------#

# This class is used to check if a contact is in the database.
class Check_Contacts:
    def __init__(self, df=None, logging=None):
        """
        The function initializes the web scraping process by setting the working directory, loading the acronyms and setting
        the variables for the web scraping

        :param df: the dataframe that contains the data to be scraped
        """
        # all the variables for the web scraping
        self.service = Service(executable_path=ChromeDriverManager().install())
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--log-level = 3")
        # setting the working directory
        basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        if os.getcwd() != basedir:
            os.chdir(basedir)
        else:
            pass
        # loading acronyms
        f = open(r'Data/common_acronyms.json')
        self.acronyms = json.load(f)
        # other variables
        self.df = df
        # logging
        self.logging = logging

    # function to show current contact list
    def get_contacts(self):
        """
        The function get_contacts() returns the dataframe df
        :return: The dataframe is being returned.
        """
        return self.df

    # function to tag loaded web elements
    def create_tags(self, text):
        """
        It loads the model and then uses it to predict the entities in the text

        :param text: The text to be processed
        :return: A list of tuples, each tuple containing the entity and its label.
        """
        ner_model = spacy.load(r"./Model/output/model-last")
        nlp = ner_model(text)
        return nlp.ents

    # function to clean html into text
    def clean_text(self, web_element):
        """
        It takes a web element, strips the whitespace, splits the text into a list, joins the list back into a string, and
        strips the whitespace again

        :param web_element: the web element you want to clean up
        :return: The cleaned text.
        """
        cleanup = web_element.text.strip()
        jumble = cleanup.split()
        cleaned = ' '.join(jumble).strip()
        return cleaned

    # function to return list of workplaces
    def list_of_firma(self, tuple):
        """
        It takes a tuple of spacy objects and returns a list of strings

        :param tuple: a tuple of spacy.tokens.span.Span objects
        :return: A list of all the workplaces in the text.
        """
        workplaces = []
        for i in tuple:
            if i.label_ == 'Firma':
                workplaces.append(i.text.lower())
        return workplaces

    # function to remove stopwords
    def cleanup(self, text):
        """
        It takes a string of text, then performs the following:

        1. Tokenizes the text and puts it into a list
        2. Removes all stop words
        3. Joins the words back into one string separated by space, and returns the result

        :param text: The text to be cleaned
        :return: A list of words that are not stopwords.
        """
        finish = []
        try:
            for token in text.split():
                if token.lower() not in stopwords_full:  # checking whether the word is not
                    finish.append(token)
        except AttributeError:
            pass
        final = ' '.join(finish)
        return final

    # function to find a common abbreviation
    def acronym_checker(self, text):
        """
        If the text is in the acronyms dictionary, return the value of the text key. Otherwise, return "No"

        :param text: The text to be checked for acronyms
        :return: The value of the key in the dictionary.
        """
        if text in self.acronyms.keys():
            return self.acronyms[text]
        else:
            return "No"

    # function to check the link of a email google search
    def check_employment(self, df_slice):
        """
        It takes a dataframe slice, and then searches for the person's name, company, and title on DuckDuckGo. It then
        scrapes the top 4 results and returns the top line, middle line, and addendum

        :param df_slice: a row of the dataframe
        :return: A dictionary with the keys 'Top Line', 'Middle Line', 'Addendum' and 'Missing element'
        """
        Top = None
        Bottom = None
        Missing = None

        # set up a fake user agent to avoid google blocking the requests
        ua = UserAgent()
        userAgent = ua.random

        self.chrome_options.add_argument(f'user-agent={userAgent}')
        driver = webdriver.Chrome(service=self.service, options=self.chrome_options)
        driver.implicitly_wait(5)
        driver.get("https://www.duckduckgo.com/")

        try:
            WebDriverWait(driver, 3).until(expected_conditions.element_to_be_clickable((By.XPATH,
                                                                                        "/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/button[2]"))).click()
        except:
            pass
        m = driver.find_element(by=By.NAME, value='q')
        m.send_keys(df_slice['Vorname'] + ' ' + df_slice['Name'] + ' ' + df_slice['Firma'])
        m.send_keys(Keys.ENTER)
        time.sleep(2)
        try:
            for i in range(4):
                website_check = driver.find_element(by=By.XPATH, value=f'//*[@id="r1-{i}"]/div[1]/div/a').text
                if 'linkedin' in website_check.lower():
                    web_element = driver.find_element(by=By.XPATH, value=f'//*[@id="r1-0"]/div[2]')
                    Top = self.clean_text(web_element)
                    if self.logging is not None:
                        self.logging.info(f'Top Line: {Top}')
                        self.logging.info("-"*50)
                    return {'Top Line': Top}

                web_element = driver.find_element(by=By.XPATH, value=f'//*[@id="r1-{i}"]/div[2]')
                dirty = self.clean_text(web_element)
                if dirty is not None:
                    if Top is not None:
                        Top += ' ' + self.cleanup(dirty)
                    else:
                        Top = self.cleanup(dirty) + ' '
                try:
                    dirty = self.clean_text(
                        web_element=driver.find_element(by=By.XPATH, value=f'//*[@id="r1-{i}"]/div[3]'))
                    Bottom += self.cleanup(dirty)
                except:
                    pass
                try:
                    dirty = self.clean_text(
                        web_element=driver.find_element(by=By.XPATH, value=f'//*[@id="r1-{i}"]/div[4]'))
                    Missing = self.cleanup(dirty)
                except:
                    pass
        except exceptions.NoSuchElementException:
            for i in range(0, 5):
                website_checker = driver.find_element(by=By.XPATH, value=f'//*[@id="r1-{i}"]/div[1]/div/a').text
                if 'linkedin' in website_checker.lower():
                    web_element = driver.find_element(by=By.XPATH, value=f'//*[@id="r1-{i}"]/div[3]/div2')
                    if self.logging is not None:
                        self.logging.info(f'Top Line: {Top}')
                        self.logging.info("-"*50)
                    Top = self.clean_text(web_element)
                    return {'Top Line': Top}
                web_element = driver.find_element(by=By.XPATH, value=f'//*[@id="r1-{i}"]/div[3]')
                dirty = self.clean_text(web_element)
                if dirty is not None:
                    if Top is not None:
                        Top += ' ' + self.cleanup(dirty)
                    else:
                        Top = self.cleanup(dirty) + ' '
        driver.close()
        if self.logging is not None:
            self.logging.info(f'Top Line: {Top}')
            self.logging.info(f'Bottom Line: {Bottom}')
            self.logging.info(f'Missing: {Missing}')
            self.logging.info("-"*50)

        if Missing is not None and 'missing' in Missing:
            return {"Top Line": Top,
                    "Middle Line": Bottom,
                    'Missing element': Missing}
        else:
            return {"Top Line": Top,
                    "Middle Line": Bottom,
                    "Addendum": Missing}

    # function to check if email is valid
    def validation(self):
        """
        This function takes a dataframe of contacts and checks if they still work at the company they are listed as working
        at
        :return: The dataframe with the updated column 'Is_Valid'
        """
        if self.df is None:
            self.load_contacts()
        for idx, row in self.df.iterrows():
            if self.logging is not None:
                self.logging.info(f"Checking now for {row[1]} {row[0]} at {row[2]} with email {row[3]}")
                self.logging.info("-" * 50)
            validation_online = self.check_employment(row)
            if 'Missing' in validation_online.values() or "It looks like there aren't many great matches for" \
                                                          "your search" in validation_online.values():
                if self.logging is not None:
                    self.logging.info(
                        f"{row['Vorname']} {row['Name']}'s' email {row['Email']} does not appear in the first search."
                        f"They may no longer work at {row['Firma']} /n" + "-" * 50)
                    continue
            check_work = find_near_matches((row[2].split()[0]).lower(),
                                           validation_online['Top Line'].lower(),
                                           max_l_dist=1)
            acronym = self.acronym_checker(row["Firma"])
            check_work_acronym = None
            if acronym != "No":
                check_work_acronym = find_near_matches(acronym,
                                                       validation_online['Top Line'],
                                                       max_l_dist=1)
            Firma_list = []
            for i in validation_online.values():
                if i is not None:
                    tags = self.create_tags(i)
                    Firma_list.append(self.list_of_firma(tags))
            l = [item for sublist in Firma_list for item in sublist]
            check_Firma = find_near_matches((row["Firma"].split()[0]).lower(), l, max_l_dist=1)
            if len(check_work) != 0 and check_work_acronym is not None and len(check_Firma) != 0:
                if self.logging is not None:
                    self.logging.info(f"{row[1]} {row[0]} definitely still works at {row[2]}")
            elif len(check_work) != 0 or check_work_acronym is not None or len(check_Firma) != 0:
                if self.logging is not None:
                    self.logging.info(f"{row[1]} {row[0]} seems to still works at {row[2]}")
            elif len(check_work) == 0 and check_work_acronym is None and len(check_Firma) == 0:
                if self.logging is not None:
                    self.logging.info(f"{row[1]} {row[0]} does not work at {row[2]} anymore")
                    self.logging.info("-" * 50)
                self.df.loc[idx, 'Is_Valid'] = 0
        if self.logging is not None:
            self.logging.info("There are {} contacts that must be updated".format(len(self.df[self.df['Is_Valid'] == 0])))
        return self.df
