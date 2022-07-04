from selenium.webdriver.common.by import By
from securer import Securer, short_wait, pause_pre_quit


class Url:
    main = "https://www.facebook.com"
    TIMELINE = f"{main}/settings?tab=timeline"
    LOCATION = f"{main}/settings?tab=location&section=location_history&view"
    ADVERTISERS = f"{main}/adpreferences/advertisers/"
    AD_TOPICS = f"{main}/adpreferences/ad_topics/"


class LoginFieldId:
    user = 'email'
    pwd = 'pass'
    submit = 'login'


# Element id and xpath
account_ = '//div[@aria-label="Account"]'
location_off_ = '//li/a/span[.="Off"]'
location_toggle_ = '//a[@rel="toggle"]'
logout_ = '//span[.="Log Out"]'
ok_pop_ = '//div[@aria-label="OK"]'
tag_review_ = '//input[@type="checkbox"]'

btn_hide, btn_fewer, btn_remove = "Hide Ads", "See Fewer", "Remove"
link_btn_map = {"ad": ((Url.ADVERTISERS, btn_hide), (Url.AD_TOPICS, btn_fewer))}


class SecureFB(Securer):
    def __init__(self):
        super().__init__('facebook')

    def connect(self):
        self.login(Url.main, LoginFieldId.user, LoginFieldId.pwd)
        self.wait_and_click(account_)

    def close(self):
        pause_pre_quit()
        self.wait_and_click(account_)
        self.wait_and_click(logout_)
        self.cleanup()

    def secure_timeline(self):
        self.driver.get(Url.TIMELINE)
        checkboxes = self.driver.find_elements(By.XPATH, tag_review_)
        for checkbox in checkboxes:
            if not checkbox.is_selected():
                checkbox.click()
                self.wait_and_click(ok_pop_)

    def secure_location(self):
        self.driver.get(Url.LOCATION)
        self.wait_for_frame(0)
        self.driver.find_element(By.XPATH, location_toggle_).click()
        self.wait_and_click(location_off_)
        self.driver.switch_to.default_content()

    def secure_ads(self):
        def uncheck(link, btn_text):
            self.driver.get(link)
            while True:
                short_wait()
                buttons = self.driver.find_elements(By.XPATH, f'//div[.="{btn_text}"]')
                if not buttons:
                    break
                for i in range(6, len(buttons), 7):
                    buttons[i].click()
                self.driver.refresh()
            return None

        for ad_link, btn_txt in link_btn_map["ad"]:
            uncheck(link=ad_link, btn_text=btn_txt)

    def secure_all(self):
        steps = [self.connect, self.secure_timeline, self.secure_location, self.secure_ads, self.close]
        for step in steps:
            step()


def main():
    my_fb = SecureFB()
    my_fb.secure_all()


if __name__ == '__main__':
    main()
