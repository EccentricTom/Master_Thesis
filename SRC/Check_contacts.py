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

class Check_Contacts:
    def __init__(self):
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

    # function to connect to sqlite database
    def get_contacts(self):
        return self.df

    # function to tag loaded web elements
    def create_tags(self, text):
        ner_model = spacy.load(r"./Model/output/model-last")
        nlp = ner_model(text)
        return nlp.ents

    # function to clean html into text
    def clean_text(self, web_element):
        cleanup = web_element.text.strip()
        jumble = cleanup.split()
        cleaned = ' '.join(jumble).strip()
        return cleaned

    # function to return list of workplaces
    def list_of_firma(self, tuple):
        workplaces = []
        for i in tuple:
            if i.label_ == 'Firma':
                workplaces.append(i.text)
        return workplaces

    # function to remove stopwords
    def cleanup(self, text):
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
        if text in self.acronyms.keys():
            return self.acronyms[text]
        else:
            return "No"

    # function to load contact table
    def load_contacts(self):
        cnx = sqlite3.connect(r"D:\HSLU_projects\Thesis\Data\Contacts.db")
        df = pd.read_sql_query('SELECT * FROM Contacts', cnx)
        cnx.close()
        self.df = df

    # function to check the link of a email google search
    def check_employment(self, df_slice):
        Top = None
        Bottom = None
        Missing = None

        #set up a fake user agent to avoid google blocking the requests
        ua = UserAgent()
        userAgent = ua.random

        self.chrome_options.add_argument(f'user-agent={userAgent}')
        driver = webdriver.Chrome(service=self.service, options=self.chrome_options)
        driver.implicitly_wait(5)
        driver.get("https://www.google.com/")

        try:
            WebDriverWait(driver, 5).until(expected_conditions.element_to_be_clickable((By.XPATH,
                                                                                        "/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/button[2]"))).click()
        except:
            pass
        m = driver.find_element(by=By.NAME, value="q")
        m = driver.find_element(by=By.NAME, value='q')
        if "info" not in df_slice['Email']:
            m.send_keys(df_slice['Email'])
        else:
            m.send_keys(df_slice['Vorname'] + ' ' + df_slice['Name'] + ' ' + df_slice['Firma'])
        m.send_keys(Keys.ENTER)
        time.sleep(5)
        try:
            WebDriverWait(driver, 5).until(expected_conditions.element_to_be_clickable((By.XPATH,
                                                                                        (expected_conditions.element_to_be_clickable((By.XPATH,
                                                                                        "/html/body/div[2]/div[3]/form"))).click()))).click()
        except:
            pass
        web_element = driver.find_element(by=By.XPATH, value='//*[@id="rso"]/div[1]/div/div[1]')
        Top = self.clean_text(web_element)
        if Top is not None:
            Top = self.cleanup(Top)
        try:
            Bottom = self.clean_text(
                web_element=driver.find_element(by=By.XPATH, value='//*[@id="rso"]/div[1]/div/div[2]'))
            Bottom = self.cleanup(Bottom)
        except:
            pass
        try:
            Missing = self.clean_text(
                web_element=driver.find_element(by=By.XPATH, value='//*[@id="rso"]/div[1]/div/div[3]'))
            Missing = self.cleanup(Missing)
        except:
            pass
        driver.close()
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
        self.load_contacts()
        with tqdm(total=len(self.df.index)) as pbar:
            for idx, row in self.df.iterrows():
                print(f"Checking now for {row[1]} {row[0]} at {row[2]} with {row[3]}")
                print(row)
                print("-----------------------------------------------")
                validation_online = self.check_employment(row)
                if 'Missing' in validation_online.values() or "It looks like there aren't many great matches for" \
                                                              "your search" in validation_online.values():
                    print(
                        f"{row['Vorname']} {row['Name']}'s' email {row['Email']} does not appear in the first search."
                        f"They may no longer work at {row['Firma']}")
                    continue
                check_work = find_near_matches(row[2].split()[0],
                                               validation_online['Top Line'],
                                               max_l_dist=1)
                print(check_work)
                acronym = self.acronym_checker(row["Firma"])
                check_work_acronym = None
                if acronym != "No":
                    check_work_acronym = find_near_matches(acronym,
                                                           validation_online['Top Line'],
                                                           max_l_dist=1)
                    print(check_work_acronym)
                Firma_list = []
                for i in validation_online.values():
                    if i is not None:
                        tags = self.create_tags(i)
                        Firma_list.append(self.list_of_firma(tags))
                l = [item for sublist in Firma_list for item in sublist]
                check_Firma = find_near_matches(row["Firma"].split()[0], l, max_l_dist=1)
                print(l)
                if len(check_work) != 0 and check_work_acronym is not None and len(check_Firma) != 0:
                    print(f"{row[1]} {row[0]} definitely still works at {row[2]}")
                elif len(check_work) != 0 or check_work_acronym is not None or len(check_Firma) != 0:
                    print(f"{row[1]} {row[0]} seems to still works at {row[2]}")
                elif len(check_work) == 0 and check_work_acronym is None and len(check_Firma) == 0:
                    print(f"{row[1]} {row[0]} does not work at {row[2]} anymore")
                    row['Is_valid'] = 0
                print("-----------------------------------------------")
                pbar.update(1)
        print("There are {} contacts that must be updated".format(self.df[self.df['Is_valid'] == 0].shape[0]))
        return self.df



