import json
import os

import yaml

with open("cred1.yml", "r") as f:
    CONFIG = yaml.full_load(f)
with open("data/qid_map.json", "r") as f:
    QID_MAP = json.load(f)
with open("data/leet_problems.json", "r") as f:
    QUESTION_BANK = json.load(f)

COMMON_HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/603.3.8 (KHTML, like Gecko) "
    "Version/10.1.2Safari/603.3.8",
}


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
