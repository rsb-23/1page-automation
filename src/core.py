import json
import os
import tomllib
from functools import partial

COMMON_HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/603.3.8 (KHTML, like Gecko) "
    "Version/10.1.2Safari/603.3.8",
}


def get_creds() -> dict:
    with open("cred.toml", "rb") as f:  # tomllib requires binary mode
        data = tomllib.load(f)
    return data


def get_json_data(filename: str) -> dict:
    with open(f"data/{filename}.json", "r") as f:
        data = json.load(f)
    return data


class Logger:
    log_folder = "log"

    def __init__(self, filename):
        self._path = f"{self.log_folder}/{filename}.log"
        self._create_file()

    def _create_file(self):
        if not os.path.exists(self.log_folder):
            os.mkdir(self.log_folder)
        if not os.path.exists(self._path):
            with open(self._path, "w") as log_head:
                log_head.write("==Logs==\n")

    def log(self, msg):
        print(msg)
        with open(self._path, "a") as logger:
            logger.write(msg)


CREDS = get_creds()
qid_map = partial(get_json_data, "qid_map")
question_map = partial(get_json_data, "leet_problems")
