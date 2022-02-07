import time
from collections import namedtuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# URLs
URL_IG = "https://www.instagram.com"
URL_EMAILS = f"{URL_IG}/emails/settings/"
URL_PUSH = f"{URL_IG}/push/web/settings/"
URL_PRIVACY = f"{URL_IG}/accounts/privacy_and_security/"

# Element id and xpath
LOGIN_FIELDS_ID = namedtuple("FieldId", "user pwd submit")("username", "password", "submit")
not_now_ = "//button[.='Not Now']"
ig_checkbox = '//input[@type="checkbox"]'
ig_label = '//label'
ig_div_label = '//div[./label/input]'
logout_ = '//div[.="Log Out"]'

PUSH_PREFS = {"likes": 0, "comments": 0, "comment_likes": 0, "like_and_comment_on_photo_user_tagged": 0,
              "follow_request_accepted": 0, "pending_direct_share": 0, "direct_share_activity": 1,
              "notification_reminders": 1, "first_post": 0, "view_count": 0, "report_updated": 1,
              "live_broadcast": 1}
PRIVACY_PREF = {"accountPrivacy": True, "activityStatus": True, "feedPostReshareDisabled": False,
                "usertagReviewEnabled": 1}
PRE_QUIT_PAUSE = 5


class SecureIG:
    def __init__(self, user, pwd):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--disable-notifications")
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        self.username = user
        self.password = pwd

    def wait_and_click(self, xpath):
        try:
            elem = self.wait.until(EC.visibility_of_element_located((By.XPATH, xpath)))
            elem.click()
        except TimeoutError:
            print(f'{xpath} click failed due to timeout')

    def select_by_name(self, name, option):
        elem = self.driver.find_elements(By.NAME, name)
        elem[option].click()

    def connect(self):
        self.driver.get(URL_IG)
        self.wait_and_click(f'//input[@name="{LOGIN_FIELDS_ID.user}"]')
        self.driver.find_element(By.NAME, LOGIN_FIELDS_ID.user).send_keys(self.username)
        self.driver.find_element(By.NAME, LOGIN_FIELDS_ID.pwd).send_keys(self.password)
        self.driver.find_element(By.XPATH, f'//button[@type="{LOGIN_FIELDS_ID.submit}"]').click()
        self.wait_and_click(not_now_)

    def close(self):
        account_ = f'//span/img[contains(@alt, "{self.username}")]'
        time.sleep(PRE_QUIT_PAUSE)
        self.wait_and_click(account_)
        self.wait_and_click(logout_)
        self.driver.quit()

    def secure_emails(self):
        self.driver.get(URL_EMAILS)
        wait_for_loading()
        labels = self.driver.find_elements(By.XPATH, ig_label)
        checkboxes = self.driver.find_elements(By.XPATH, ig_checkbox)
        assert len(labels) == len(checkboxes)
        self.wait.until(EC.element_to_be_clickable(labels[0]))
        for label, checkbox in zip(labels, checkboxes):
            if checkbox.is_selected():
                label.click()

    def secure_push(self):
        self.driver.get(URL_PUSH)
        wait_for_loading()
        for name, pref in PUSH_PREFS.items():
            self.select_by_name(name, pref)

    def secure_privacy(self):
        self.driver.get(URL_PRIVACY)
        wait_for_loading()
        divs = self.driver.find_elements(By.XPATH, ig_div_label)
        for div in divs:
            elem = div.find_element(By.TAG_NAME, 'input')
            if elem.is_selected() != PRIVACY_PREF[div.get_attribute("id")]:
                div.click()
                time.sleep(2)
        review = "usertagReviewEnabled"
        self.select_by_name(review, PRIVACY_PREF[review])

    def secure_all(self):
        steps = [self.connect, self.secure_emails, self.secure_push, self.secure_privacy, self.close]
        for step in steps:
            step()


def wait_for_loading(): time.sleep(5)


if __name__ == '__main__':
    username = input("Enter your IG username : ")
    password = input("Enter your password : ")
    my_ig = SecureIG(username, password)
    my_ig.secure_all()
