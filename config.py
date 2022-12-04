import json
import os

import yaml

with open("cred-personal.yml", "r") as f:
    CONFIG = yaml.full_load(f)
with open("data/qid_map.json", "r") as f:
    QID_MAP = json.load(f)
with open("data/leet_problems.json", "r") as f:
    QUESTION_BANK = json.load(f)


class Logger:
    log_folder = "log"

    def __init__(self, filename):
        self._path = f"{self.log_folder}/{filename}.log"
        self._create_file()

    def _create_file(self):
        if not os.path.exists(self.log_folder):
            os.mkdir(self.log_folder)
        if not os.path.exists(self._path):
            with open(self._path, "w") as f:
                f.write("==Logs==\n")

    def log(self, msg):
        print(msg)
        with open(self._path, "a") as f:
            f.write(msg)
