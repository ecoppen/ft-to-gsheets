import logging
import os
import sqlite3
from pathlib import Path

import gspread
import pandas as pd

secrets_file = Path(Path.home(), "ft-to-gsheets", "client_secret.json")
logs_file = Path(Path.home(), "ft-to-gsheets", "log.txt")
freqtrade_database = Path(Path.home(), "freqtrade", "tradesv3.sqlite")
google_workbook_name = ""
google_workbook_sheet_name = ""

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=os.environ.get("LOGLEVEL", "INFO"),
    handlers=[logging.FileHandler(logs_file), logging.StreamHandler()],
)

log = logging.getLogger(__name__)


def check_file_exists(file):
    return file.is_file()


def check_authorisation(file):
    try:
        gspread.service_account(filename=file)
        return True
    except ValueError as e:
        log.error(f"Loading {file} has failed: {e}")
    return False


def setup_new_workbook(service_account, workbook_name, sheet_name):
    sh = service_account.create(workbook_name)
    log.info(f"Created workbook - {workbook_name}")
    worksheet = sh.sheet1
    worksheet.update_title("Summary")
    log.info("Added worksheet - Summary")
    sh.add_worksheet(title=sheet_name, rows=1000, cols=30)
    log.info(f"Added worksheet - {sheet_name}")
    sh.add_worksheet(title="data processing", rows=1000, cols=30)
    log.info("Added worksheet - data processing")


def setup_new_worksheet(service_account, workbook_name, sheet_name):
    sh = service_account.create(workbook_name)
    worksheet_list = sh.worksheets()
    sheets_to_create = ["Summary", sheet_name, "data processing"]
    for sheet in sheets_to_create:
        if sheet not in worksheet_list:
            sh.add_worksheet(title=sheet_name, rows=1000, cols=30)
            log.info(f"Added worksheet - {sheet_name}")
    if "Sheet1" in worksheet_list:
        sh.del_worksheet("Sheet1")
        log.info("Deleted worksheet - Sheet1")


def check_workbook_sheet_exists(file, recheck_workbook=False, recheck_worksheet=False):
    try:
        gc = gspread.service_account(filename=str(file))
        gc.open(google_workbook_name).worksheet(google_workbook_sheet_name)
        return True
    except gspread.exceptions.SpreadsheetNotFound:
        log.error(f"This workbook does not exist: {google_workbook_name}")
        if not recheck_workbook:
            log.info(f"Attempting to setup: {google_workbook_name}")
            setup_new_workbook(
                service_account=gc,
                workbook_name=google_workbook_name,
                worksheet_name=google_workbook_sheet_name,
            )
            return check_workbook_sheet_exists(file=file, recheck_workbook=True)
    except gspread.exceptions.WorksheetNotFound:
        log.error(f"This worksheet does not exist: {google_workbook_sheet_name}")
        if not recheck_worksheet:
            log.info(f"Attempting to setup: {google_workbook_sheet_name}")
            setup_new_worksheet(
                service_account=gc,
                workbook_name=google_workbook_name,
                worksheet_name=google_workbook_sheet_name,
            )
            return check_workbook_sheet_exists(file=file, recheck_worksheet=True)
    return False


def check_database_connection(file):
    try:
        sqlite3.connect(
            f"file://{file}?mode=ro",
            uri=True,
            isolation_level=None,
            detect_types=sqlite3.PARSE_COLNAMES,
        )
        return True
    except sqlite3.OperationalError as e:
        log.error(f"Loading {file} has failed: {e}")
    return False


def initial_checks(google_file, freqtrade_file):
    if check_file_exists(google_file):
        if check_authorisation(google_file):
            if google_workbook_name != "" and google_workbook_sheet_name != "":
                if check_workbook_sheet_exists(google_file):
                    if check_file_exists(freqtrade_file):
                        if check_database_connection(freqtrade_file):
                            return True
                        else:
                            log.error(
                                f"This isn't a compatible database file: {freqtrade_file}"
                            )
                    else:
                        log.error(
                            f"Freqtrade database does not exist at this location, please check path: {freqtrade_database}"
                        )
                else:
                    log.error("Error finding or setting up Google Sheets")
            else:
                log.error("The Google Sheet has not been setup or referenced correctly")
        else:
            log.error(
                "Please fix the json file with the client secret - https://pygsheets.readthedocs.io/en/latest/authorization.html"
            )
    else:
        log.error(
            "Please fix the json file with the client secret - https://pygsheets.readthedocs.io/en/latest/authorization.html"
        )
    return False


def format_pre_import(base_list):
    formatted_list = []
    for sublist in base_list:
        sublist = ["-" if str(data) == "nan" else data for data in sublist]
        formatted_list.append(sublist)
    return formatted_list


def main():
    log.info("Starting transfer")
    if initial_checks(google_file=secrets_file, freqtrade_file=freqtrade_database):
        log.info("Checks passed")
        conn = sqlite3.connect(
            f"file://{freqtrade_database}?mode=ro",
            uri=True,
            isolation_level=None,
            detect_types=sqlite3.PARSE_COLNAMES,
        )

        db_df = pd.read_sql_query("SELECT * FROM trades", conn)
        gc = gspread.service_account(filename=str(secrets_file))
        wks = gc.open(google_workbook_name).worksheet(google_workbook_sheet_name)
        wks.clear()
        wks.update(
            "A1",
            [db_df.columns.values.tolist()] + format_pre_import(db_df.values.tolist()),
            value_input_option="USER_ENTERED",
        )
    log.info("Transfer complete")


if __name__ == "__main__":
    main()
