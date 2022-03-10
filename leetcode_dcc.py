import requests
import yaml

with open("config.yml", 'r') as f:
    CONFIG = yaml.full_load(f)['leetcode']
LANG = CONFIG['global_lang']


def logger(msg):
    with open('log.txt', 'a') as f:
        f.write(msg)


def copy_and_submit(qid, qname):
    cookies = CONFIG["cookies"]

    old_submission = f"https://leetcode.com/submissions/latest/?qid={qid}&lang={LANG}"
    page = requests.get(old_submission, cookies=cookies)

    if page.status_code == 200:
        solution = page.json()["code"]

        new_submission = f"https://leetcode.com/problems/{qname}/submit/"
        headers = {"referer": f"https://leetcode.com/problems/{qname}/submissions/",
                   "x-csrftoken": cookies["csrftoken"]}
        payload = {"lang": LANG, "question_id": qid, "typed_code": solution}
        page = requests.post(new_submission, headers=headers, cookies=cookies, json=payload, timeout=60)
        print(page.status_code, page.text)
        result = "Success"
    elif page.status_code == 404:
        result = f"No old solution found for {qid}. {qname}"
    else:
        result = f"Unexpected issue - {page.status_code}"
    logger(result + '\n')


def get_question():
    url_query = "https://leetcode.com/graphql/"
    payload = {"query": "\n    query questionOfToday {\n  activeDailyCodingChallengeQuestion {\n    date\n    "
                        "link\n    question {\n      frontendQuestionId: questionFrontendId\n      "
                        "title\n      titleSlug\n      "
                        "\n    }\n  }\n}\n    ",
               "variables": {}}

    page = requests.post(url_query, json=payload)
    result = page.json()["data"]["activeDailyCodingChallengeQuestion"]
    logger(f"{result['date']} : ")
    question = result["question"]
    return question["frontendQuestionId"], question["titleSlug"]


if __name__ == '__main__':
    question_id, question_title = get_question()
    copy_and_submit(question_id, question_title)
