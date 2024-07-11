""" leetcode_dcc.py:
To re-submit old solution for LeetCode Daily Coding Challenges

Info -
1. Store cookies value in cred.yml
2. Update LEETCODE_SESSION value, in case of failure.

Suggestion - Use Task Scheduler/ Cron Job to run this script daily
"""

from datetime import datetime
from time import sleep

import requests

from config import COMMON_HEADERS, CONFIG, Logger

LEET_CONFIG = CONFIG["leetcode"]
logger = Logger("leet_dcc")

BASE_URL = "https://leetcode.com"
QUERY_URL = f"{BASE_URL}/graphql"
INVALID_SESSION_COOKIE = "Update LEETCODE_SESSION cookie"


class Question:
    def __init__(self, date, question):
        self._date = date
        self.difficulty = question["difficulty"]
        self.display_qid = question["questionFrontendId"]
        self.qid = question["questionId"]
        self.title = question["titleSlug"]

    @property
    def date(self):
        return datetime.strptime(self._date, "%Y-%m-%d").strftime("%d %b")


def get_dcc_question():
    payload = {
        "query": "query questionOfToday {activeDailyCodingChallengeQuestion{date question "
        "{questionFrontendId questionId titleSlug difficulty} }}"
    }
    json_data = s.post(QUERY_URL, json=payload).json()["data"]
    q = Question(**json_data["activeDailyCodingChallengeQuestion"])

    logger.log(f"{q.date}: _{q.difficulty[0]}_ | {q.display_qid:>4}: {q.title:<40} | ")
    return q.qid, q.title


def official_solution(slug):
    editorial_payload = {
        "query": "query officialSolution($titleSlug: String!) {question(titleSlug: $titleSlug){solution{content}}}",
        "variables": {"titleSlug": slug},
    }
    editorial = s.post(QUERY_URL, json=editorial_payload)
    if "playground" not in editorial.text:
        return None
    solution_uuid = editorial.text.split("playground/")[-1][:8]

    solution_payload = {
        "query": f'query fetchPlayground {{allPlaygroundCodes(uuid: "{solution_uuid}") {{code langSlug}} }}'
    }
    solution = s.post(QUERY_URL, json=solution_payload).json()["data"]
    py_solutions = [*filter(lambda x: x["langSlug"] == "python3", solution["allPlaygroundCodes"])]
    return py_solutions[-1]["code"] if py_solutions else None


def get_solution(qid, slug) -> str | None:
    submission = s.get(f"{BASE_URL}/submissions/latest/?qid={qid}&lang={lang}")
    if submission.status_code == 401:
        raise ValueError(INVALID_SESSION_COOKIE)
    if submission.status_code == 200:
        return submission.json()["code"]

    return official_solution(slug)


def is_submission_accepted(sub_id: int) -> bool:
    def check():
        _check = s.get(f"{BASE_URL}/submissions/detail/{sub_id}/check/")
        logger.log(f"{_check} {_check.content}")
        return _check.json()

    resp = {"state": ""}
    while resp["state"] != "SUCCESS":
        sleep(0.5)
        resp = check()

    status_msg = resp["status_msg"]
    logger.log(f"{status_msg=}")
    return status_msg == "Accepted"


def submit_solution(qid, title_slug, solution):
    _title_url = f"{BASE_URL}/problems/{title_slug}"

    s.headers.update(
        {
            "referer": f"{_title_url}/submissions/",
            "x-csrftoken": s.cookies["csrftoken"],
            "X-Newrelic-Id": cookies["newrelic_id"],
            **COMMON_HEADERS,
        }
    )
    payload = {"lang": lang, "question_id": qid, "typed_code": solution}
    page = s.post(f"{_title_url}/submit/", json=payload, timeout=60)

    if page.status_code != 200:
        return f"{page.status_code} - {INVALID_SESSION_COOKIE}"
    return (
        f">SOLVED< {page.text}"
        if is_submission_accepted(sub_id=page.json()["submission_id"])
        else "Wrong Submission, solve manually."
    )


if __name__ == "__main__":
    cookies, lang = LEET_CONFIG["cookies"], LEET_CONFIG["global_lang"]

    with requests.Session() as s:
        for k, v in cookies.items():
            s.cookies.set(k, v)
        que_id, title = get_dcc_question()
        dcc_solution = get_solution(que_id, title)
    if dcc_solution:
        result = submit_solution(que_id, title, dcc_solution)
    else:
        result = f">SOLUTION_NOT_FOUND< {que_id=}"

    logger.log(result + "\n")
    s.close()  # Closing session explicitly
