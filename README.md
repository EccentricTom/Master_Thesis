# Master’s Thesis – Contact Checker (Data Validation + Replacement Pipeline)

This repository contains code from my Master’s thesis work (HSLU) focused on building a practical data tooling workflow to **validate and maintain a contact database**.

At a high level, the system:
- ingests contacts (CSV/JSON) into a SQLite database,
- periodically checks whether a contact is still associated with the listed organisation (via web search),
- flags likely-invalid contacts,
- proposes replacements by finding an alternative contact + inferring the organisation’s email format,
- stores updated contacts and exposes simple API endpoints to retrieve them.

It’s an academic / prototype codebase, but it’s representative of the kind of “data plumbing + validation + automation” work I enjoy: **quality checks, dedup/near-match logic, lightweight auditing, and turning workflows into repeatable systems.**

---

## What to look at (quick tour)

If you’re skimming for “signal”, these are the key files:

- `SRC/Notebooks/app.py`  
  Flask API + background thread to run contact validation in batches (and log outcomes).

- `SRC/Notebooks/Check_contacts_bing.py` (and/or `Check_contacts.py`)  
  Contact validation logic (search, parse results, determine whether a contact is likely valid).

- `SRC/Notebooks/Find_and_replace.py`  
  Replacement workflow: infer email formatting rules, find candidate contacts, create new contact entries.
  Includes rule-based email generation and entity extraction.

- `SRC/Notebooks/data_handler.py`  
  SQLite persistence layer (loading/saving contact tables).

- `Plan_for_app.txt`  
  The intended workflow and design notes (useful context when reading the code).

---

## How it works (high level)

1. **Load contacts** into SQLite (`Contacts` table).
2. **Validate contacts** by running a web search and comparing returned context against expected company/name signals.
3. For invalid contacts (`Is_Valid = 0`):
   - infer the **organisation’s email format** from known contacts,
   - search for a plausible replacement contact,
   - extract a person name using NER,
   - generate the new email based on the inferred format,
   - write replacements to the updated dataset.
4. Expose updated contacts via a small Flask API.

---

## Repo structure

/myproject
├── /src
|   ├── Notebooks
│   |   └── Document_creator.ipynb
│   |   └── EDA_and_Cleaning.ipynb
│   |   └── Playground.ipynb
│   |   └── Spacy_model_training.ipynb
│   ├── Check_contacts.py
│   ├── Check_contacts_bing.py
│   ├── DDG_API_Test.py
│   ├── Find_and_replace.py
│   ├── Initialise_contacts.py
│   ├── app.py
│   ├── backup.py
│   └── data_handler.py
├── .gitignore
├── Plan_for_app.txt
├── Requirements.txt
└── event_log.txt


---

## Running locally (minimal)

> Note: this code was written in an academic context and may require small path/config adjustments
> (e.g., local working directory paths, database file locations, Chrome driver behaviour).

### 1) Install dependencies
```bash
python -m venv .venv
source .venv/bin/activate   # (Windows: .venv\Scripts\activate)
python -m pip install --upgrade pip
pip install -r Requirements.txt
```

### 2) Install SpaCy models
Some scripts expect both English + German models:
``` bash
python -m spacy download en_core_web_sm
python -m spacy download de_core_news_lg
```

### 3) System Requirement: Chrome/Chromium
Parts of the validation/replacement flow use Selenium with a headless Chrome browser.

- Install Google Chrome (or Chromium) locally.
- If you run into driver issues, see the note below on optional dependencies.

### 4) Initialise the SQLite DB
``` bash
python SRC/Initialise_contacts.py
```

### 5) Run the API + background checker
``` bash
python SRC/app.py
```
---
## Troubleshootiung / common issues

### Missing Packages (webdriver_manager, fake_useragent)
Some scripts import:

- webdriver_manager (for ChromeDriver)
- fake_useragent (to randomise the user agent)

If you get import errors, install them:
```bash
pip install webdriver-manager fake-useragent
```

### Prototype Paths
Some scripts contain hard-coded Windows paths (e.g., D:\HSLU_Projects\Thesis).
You may need to adjust these to match your local environment.

---

## API Endpoints
- PUT /update_contacts_json — append contacts from JSON payload
- PUT /update_contacts_csv — append contacts from CSV payload (wrapped in JSON)
- POST /contacts_json_replace — replace the full contacts table (wipe + insert)
- POST /contacts_csv_replace — replace the full contacts table (wipe + insert)
- GET /request_updated_contacts — retrieve updated contacts as JSON
(The request/response formats are described inline in app.py.)

## Notes/Caveats
- Web automation & rate limits: the validation/replacement logic uses web search and browser automation. If you adapt this, you should respect platform terms and add careful throttling/backoff.
- Prototype quality: paths, naming, packaging, and test coverage reflect thesis-stage code. If I were productising it today, I’d:
  - remove hard-coded paths and use a config file,
  - package the project (pyproject.toml), add typing + linting,
  - add unit tests around the email-rule inference and validation heuristics,
  - containerise the service for reproducible runs,
  - add a small audit report output (HTML/CSV) for easy review.

## Why this repo is relevant for data work
Even though the domain is “contact management”, the patterns are the same as dataset/production data workflows:
- ingestion → validation → correction → versioned output,
- near-duplicate handling and rule-based normalization,
- lightweight auditing outputs and operator-friendly logging,
- turning a manual workflow into a repeatable system.
