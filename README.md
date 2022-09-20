<h1 align="center">
FT to gSheets
</h1>

<p align="center">
A python (3.10+) script to transfer your trade data from a <a href="https://www.freqtrade.io/en/stable/">freqtrade</a> SQL database to <a href="https://www.google.co.uk/sheets/about/">Google Sheets</a>.
</p>
<p align="center">
<img alt="GitHub Pipenv locked Python version" src="https://img.shields.io/github/pipenv/locked/python-version/ecoppen/ft-to-gsheets">
<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
</p>

### Installation instructions 

- Clone the repo `git clone https://github.com/ecoppen/ft-to-gsheets.git`
- Go into the ft-to-gsheets folder `cd ft-to-gsheets`
- Install pipenv `pip install pipenv`
- Adjust the Pipfile if you want to use Python 3.8 or 3.9 (last line) `nano edit Pipfile`
- Install the requirements `pipenv install`
- Add/check variables for Google Sheets (lines 9-12) `nano edit transfer.py`
- Create `client_secret.json` using instructions from https://pygsheets.readthedocs.io/en/latest/authorization.html `nano client_secret.json` 

### How to run manually

- `pipenv run python transfer.py`

### How to run on cron

- Edit cron `crontab -e`
- Add line at bottom `3-59/5 * * * * /bin/bash -c "/root/ft-to-gsheets/transfer.sh"`
- `3-59/5 * * * *` means every 5 minutes starting at minute 3, visit here to decide your own `https://crontab.guru/#3-59/5_*_*_*_*`
- Install requirements to the pipenv `/usr/local/bin/pipenv install gspread pandas`
- `/usr/local/bin/pipenv` is where pipenv can be found, type `which pipenv` to find your own
- Make the shell script executable `chmod +x /root/ft-to-gsheets/transfer.sh`
- Edit the `transfer.sh` script as necessary if you have moved/changed the directory structure
