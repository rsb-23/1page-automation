from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from securer import Securer, short_wait, long_wait, pause_pre_quit


class Url:
    main = "https://www.instagram.com"
    emails = f"{main}/emails/settings/"
    push = f"{main}/push/web/settings/"
    privacy = f"{main}/accounts/privacy_and_security/"


class LoginFieldId:
    user = 'username'
    pwd = 'password'
    submit = 'submit'


# Element id and xpath
not_now_ = "//button[.='Not Now']"
ig_checkbox_ = '//input[@type="checkbox"]'
ig_label_ = '//label'
ig_div_label_ = '//div[@id and ./label/input]'
ig_toggle_ = '//label[./input[@type="checkbox"] and ./span]'
logout_ = '//div[.="Log Out"]'

PUSH_PREFS = {"likes": 0, "comments": 0, "comment_likes": 0, "like_and_comment_on_photo_user_tagged": 0,
              "follow_request_accepted": 0, "pending_direct_share": 0, "direct_share_activity": 1,
              "notification_reminders": 1, "first_post": 0, "view_count": 0, "report_updated": 1,
              "live_broadcast": 1}
PRIVACY_PREF = {"accountPrivacy": True, "activityStatus": True, "feedPostReshareDisabled": False,
                "usertagReviewEnabled": 1}


class SecureIG(Securer):
    def __init__(self):
        super().__init__('instagram')

    def select_by_name(self, name, option):
        elem = self.driver.find_elements(By.NAME, name)
        elem[option].click()

    def connect(self):
        self.driver.get(Url.main)
        self.wait_and_click(f'//input[@name="{LoginFieldId.user}"]')
        self.driver.find_element(By.NAME, LoginFieldId.user).send_keys(self.username)
        self.driver.find_element(By.NAME, LoginFieldId.pwd).send_keys(self.password)
        self.driver.find_element(By.XPATH, f'//button[@type="{LoginFieldId.submit}"]').click()
        self.wait_and_click(not_now_)

    def close(self):
        account_ = f'//span/img[contains(@alt, "{self.username}")]'
        pause_pre_quit()
        self.wait_and_click(account_)
        self.wait_and_click(logout_)
        self.cleanup()

    def secure_emails(self):
        self.driver.get(Url.emails)
        long_wait()
        labels = self.driver.find_elements(By.XPATH, ig_label_)
        checkboxes = self.driver.find_elements(By.XPATH, ig_checkbox_)
        assert len(labels) == len(checkboxes)
        self.wait.until(EC.element_to_be_clickable(labels[0]))
        for label, checkbox in zip(labels, checkboxes):
            if checkbox.is_selected():
                label.click()

    def secure_push(self):
        self.driver.get(Url.push)
        long_wait()
        for name, pref in PUSH_PREFS.items():
            self.select_by_name(name, pref)

    def secure_privacy(self):
        self.driver.get(Url.privacy)
        long_wait()
        divs = self.driver.find_elements(By.XPATH, ig_div_label_)
        for div in divs:
            elem = div.find_element(By.TAG_NAME, 'input')
            if elem.is_selected() != PRIVACY_PREF[div.get_attribute("id")]:
                div.click()
                short_wait()
        review = "usertagReviewEnabled"
        self.select_by_name(review, PRIVACY_PREF[review])
        short_wait()
        labels = self.driver.find_elements(By.XPATH, ig_toggle_)
        for label in labels:
            elem = label.find_element(By.TAG_NAME, 'input')
            if elem.is_selected():
                label.click()
                short_wait()

    def secure_all(self):
        steps = [self.connect, self.secure_emails, self.secure_push, self.secure_privacy, self.close]
        for step in steps:
            step()
            short_wait()


def main():
    my_ig = SecureIG()
    my_ig.secure_all()


if __name__ == '__main__':
    main()
