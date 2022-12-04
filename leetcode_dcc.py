""" leetcode_dcc.py:
To re-submit old solution for LeetCode Daily Coding Challenges

Settings-
1. Check the availability of data/qid_map.json and cred.yml
2. Add cookies value in cred.yml
3. Update LEETCODE_SESSION value, in case of failure.

Suggestion - Use Task Scheduler/ Cron Job to run this script daily
"""
import requests

from config import CONFIG, Logger

CONFIG = CONFIG["leetcode"]
logger = Logger("leet_dcc")


def copy_and_submit(qid, title_slug):
    cookies = CONFIG["cookies"]
    lang = CONFIG["global_lang"]

    old_submission = f"https://leetcode.com/submissions/latest/?qid={qid}&lang={lang}"
    page = requests.get(old_submission, cookies=cookies)

    if page.status_code == 200:
        solution = page.json()["code"]

        new_submission = f"https://leetcode.com/problems/{title_slug}/submit/"
        headers = {
            "referer": f"https://leetcode.com/problems/{title_slug}/submissions/",
            "x-csrftoken": cookies["csrftoken"],
        }
        payload = {"lang": lang, "question_id": qid, "typed_code": solution}
        page = requests.post(
            new_submission, headers=headers, cookies=cookies, json=payload, timeout=60
        )

    return page.status_code, page.text


def get_active_question():
    url_query = "https://leetcode.com/graphql/"
    payload = {
        "query": "\n query questionOfToday {\n activeDailyCodingChallengeQuestion {\n date\n question "
        "{\n frontendQuestionId: questionFrontendId\n questionId\n titleSlug\n difficulty\n \n }\n }\n}\n",
        "variables": {},
    }

    page = requests.post(url_query, json=payload)
    result = page.json()["data"]["activeDailyCodingChallengeQuestion"]
    logger.log(f"{result['date']} : ")
    question = result["question"]

    return question.values()  # order as in payload["query"]


if __name__ == "__main__":
    display_qid, qid, title_slug, question_difficulty = get_active_question()
    status_code, response_text = copy_and_submit(qid, title_slug)

    if status_code == 200:
        result = f"{status_code} {response_text}"
    elif status_code == 404:
        result = f"No old solution found for {qid=}. [{display_qid}: {title_slug}]"
    else:
        result = f"{status_code} - Try changing LEETCODE_SESSION value using cookies"
    logger.log(f"{result} ({question_difficulty}) \n")
