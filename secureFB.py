import time
from collections import namedtuple
from selenium import webdriver
from selenium.webdriver.common.by import By


class SecureFB:
    def __init__(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--disable-notifications")
        self.driver = webdriver.Chrome(options=chrome_options)

    def connect(self):
        self.driver.get(FB_CRED.url)
        self.driver.find_element(By.ID, LOGIN_FIELDS_ID.user).send_keys(FB_CRED.username)
        self.driver.find_element(By.ID, LOGIN_FIELDS_ID.pwd).send_keys(FB_CRED.password)
        self.driver.find_element(By.NAME, LOGIN_FIELDS_ID.submit).click()

    def close(self):
        time.sleep(PRE_QUIT_PAUSE)
        self.driver.find_element(By.XPATH, '//div[@aria-label="Account"]').click()
        quick_wait()
        self.driver.find_element(By.XPATH, '//span[.="Log Out"]').click()
        self.driver.quit()

    def secure_ads(self):
        def uncheck(link, btn_text):
            self.driver.get(link)
            short_wait()

            if btn_text == "Hide Ads":
                btn_more = self.driver.find_elements(By.XPATH, f'//div[.="See More"]')
                if len(btn_more) > 1:
                    btn_more[1].click()

            buttons = self.driver.find_elements(By.XPATH, f'//div[.="{btn_text}"]')
            for i in range(6, len(buttons), 7):
                buttons[i].click()
            return None

        ad_sections = (("https://www.facebook.com/adpreferences/advertisers/", "Hide Ads"),
                       ("https://www.facebook.com/adpreferences/ad_topics/", "See Fewer"))
        for ad_link, btn_txt in ad_sections:
            uncheck(link=ad_link, btn_text=btn_txt)
            long_wait()

    def secure_timeline(self):
        self.driver.get("https://www.facebook.com/settings?tab=timeline")
        short_wait()
        checkboxes = self.driver.find_elements(By.XPATH, "//input[@type='checkbox']")

        for checkbox in checkboxes:
            if not checkbox.is_selected():
                checkbox.click()

    def secure_location(self):
        self.driver.get("https://www.facebook.com/settings?tab=location&section=location_history&view")
        short_wait()
        self.driver.switch_to.frame(0)
        self.driver.find_element(By.XPATH, '//a[@rel="toggle"]').click()
        quick_wait()
        self.driver.find_element(By.XPATH, '//li/a/span[.="Off"]').click()
        self.driver.switch_to.default_content()

    def secure_all(self):
        for function in (self.secure_timeline, self.secure_location, self.secure_ads):
            long_wait()
            function()


def quick_wait(): time.sleep(1)
def short_wait(): time.sleep(3)
def long_wait(): time.sleep(5)


if __name__ == '__main__':
    Credential = namedtuple("Credential", "url username, password")
    SignIn = namedtuple("SignIn", "user pwd submit")

    username = input("Enter your FB username : ")
    password = input("Enter your password : ")

    FB_CRED = Credential("https://www.facebook.com", username, password)
    LOGIN_FIELDS_ID = SignIn("email", "pass", "login")
    PRE_QUIT_PAUSE = 10

    my_fb = SecureFB()
    my_fb.connect()
    my_fb.secure_all()
    my_fb.close()
