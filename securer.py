from functools import partial
from time import sleep

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config import CONFIG

short_wait = partial(sleep, 2)
long_wait = partial(sleep, 5)
pause_pre_quit = partial(sleep, 5)


def fetch_creds(social_media):
    cred = CONFIG[social_media]
    return cred["user"], cred["pwd"]


class Securer:
    def __init__(self, social_media):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("start-maximized")
        chrome_options.add_argument("--disable-notifications")

        chrome_options.binary_location = r"C:\Program Files\Google\Chrome Beta\Application\chrome.exe"
        chrome_service = Service(CONFIG["driver_path"])

        self.driver = webdriver.Chrome(options=chrome_options, service=chrome_service)
        self.wait = WebDriverWait(self.driver, 10)
        self.username, self.password = fetch_creds(social_media)
        self.logger = open(f"{social_media}_settings.log", "w")

    def wait_and_click(self, xpath, click=True):
        try:
            elem = self.wait.until(EC.visibility_of_element_located((By.XPATH, xpath)))
            if click:
                elem.click()
        except TimeoutError:
            print(f"{xpath} click failed due to timeout")

    def wait_for_frame(self, frame_id):
        self.wait.until(EC.frame_to_be_available_and_switch_to_it(frame_id))

    def log(self, txt):
        self.logger.write(txt + "\n")

    def cleanup(self):
        self.logger.close()
        self.driver.quit()
        print("Logged Out Successfully")

    def login(self, url, user_id, pwd_id):
        self.driver.get(url)
        self.driver.find_element(By.ID, user_id).send_keys(self.username)
        self.driver.find_element(By.ID, pwd_id).send_keys(self.password, Keys.ENTER)
        short_wait()
