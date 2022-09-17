import logging
import os
import sqlite3
from pathlib import Path

import gspread
import pandas as pd

secrets_file = Path("client_secret.json")
freqtrade_database = Path(Path.home(), "freqtrade", "tradesv3.sqlite")
google_workbook_name = ""
google_workbook_sheet_name = ""

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=os.environ.get("LOGLEVEL", "INFO"),
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


def check_workbook_sheet_exists(file):
    try:
        gc = gspread.service_account(filename=str(file))
        gc.open(google_workbook_name).worksheet(google_workbook_sheet_name)
        return True
    except gspread.exceptions.SpreadsheetNotFound:
        log.error(f"This workbook does not exist: {google_workbook_name}")
    except gspread.exceptions.WorksheetNotFound:
        log.error(f"This worksheet does not exist: {google_workbook_sheet_name}")
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
            if (
                google_workbook_name != ""
                and google_workbook_sheet_name != ""
                and check_workbook_sheet_exists(google_file)
            ):
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
                log.error("The Google Sheet has not been setup or referenced correctly")
        else:
            log.error(
                "Please fix the client_secret.json file - https://pygsheets.readthedocs.io/en/latest/authorization.html"
            )
    else:
        log.error(
            "Please create the client_secret.json file - https://pygsheets.readthedocs.io/en/latest/authorization.html"
        )
    return False


def main():
    if initial_checks(google_file=secrets_file, freqtrade_file=freqtrade_database):

        conn = sqlite3.connect(
            f"file://{freqtrade_database}?mode=ro",
            uri=True,
            isolation_level=None,
            detect_types=sqlite3.PARSE_COLNAMES,
        )

        db_df = pd.read_sql_query("SELECT * FROM trades", conn)
        gc = gspread.service_account(filename=str(secrets_file))
        wks = gc.open(google_workbook_name).worksheet(google_workbook_sheet_name)
        wks.update(
            range_name="A1",
            values=[db_df.columns.values.tolist()] + db_df.values.tolist(),
            value_input_option="USER_ENTERED",
        )


if __name__ == "__main__":
    main()
