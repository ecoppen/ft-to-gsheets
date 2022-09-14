from pathlib import Path

import pygsheets

secrets_file = Path("client_secret.json")


def check_file_exists(file):
    return file.is_file()


def main():
    if check_file_exists(secrets_file):
        print("ok")
    else:
        print(
            "Please create the client_secret.json file - https://pygsheets.readthedocs.io/en/latest/authorization.html"
        )


if __name__ == "__main__":
    main()
