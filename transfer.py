import logging
import os
import sqlite3
from pathlib import Path

import gspread
import pandas as pd

secrets_file = Path("client_secret.json")
freqtrade_database = Path(Path.home(), "freqtrade", "tradesv3.sqlite")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=os.environ.get("LOGLEVEL", "INFO"),
)

log = logging.getLogger(__name__)


def paste_csv(csv_file, sheet, cell):
    if "!" in cell:
        (tabName, cell) = cell.split("!")
        wks = sheet.worksheet(tabName)
    else:
        wks = sheet.sheet1
    (firstRow, firstColumn) = gspread.utils.a1_to_rowcol(cell)

    with open(csv_file, "r") as f:
        csv_contents = f.read()
    body = {
        "requests": [
            {
                "pasteData": {
                    "coordinate": {
                        "sheetId": wks.id,
                        "rowIndex": firstRow - 1,
                        "columnIndex": firstColumn - 1,
                    },
                    "data": csv_contents,
                    "type": "PASTE_NORMAL",
                    "delimiter": ",",
                }
            }
        ]
    }
    return sheet.batch_update(body)


def check_file_exists(file):
    return file.is_file()


def check_authorisation(file):
    try:
        gspread.service_account(filename=file)
        return True
    except ValueError as e:
        log.error(f"Loading {file} has failed: {e}")
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
        db_df.to_csv("db.csv", index=False)

        client = gspread.service_account(filename=str(secrets_file))
        sheet = client.open("Cryptobot")

        ws = sheet.worksheet("binance-usdt-trades")
        paste_csv("db.csv", ws, "A1")


if __name__ == "__main__":
    main()
