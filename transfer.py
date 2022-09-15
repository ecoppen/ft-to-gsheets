import logging
import os
from pathlib import Path

import pygsheets
import sqlalchemy as db
from sqlalchemy import exc

secrets_file = Path("client_secret.json")
freqtrade_database = Path(Path.home(), "freqtrade", "tradesv3.sqlite")

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
        pygsheets.authorize(service_file=file)
        return True
    except ValueError as e:
        log.error(f"Loading {file} has failed: {e}")
    return False


def check_database_connection(file):
    try:
        engine = db.create_engine(f"sqlite:///{file}.db?check_same_thread=false")
        engine.table_names()
        return True
    except exc.OperationalError as e:
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
                        f"This isn't a comptaible database file: {freqtrade_file}"
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
        client = pygsheets.authorize(service_file=secrets_file)
        engine = db.create_engine(
            f"sqlite:///{freqtrade_database}.db?check_same_thread=false"
        )
        print(engine.table_names())
        sh = client.open("Cryptobot")
        worksheet = sh.worksheet("title", "bi-usdt-trades")
        sh.del_worksheet(worksheet)


if __name__ == "__main__":
    main()
