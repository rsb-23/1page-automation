import re

from selenium.webdriver.common.by import By

from securer import Securer, long_wait, pause_pre_quit, short_wait


class Url:
    main = "https://www.linkedin.com"
    ad_base_url = "https://www.linkedin.com/psettings/advertising"
    ad_types = [
        "profile-data",
        "li-enterprise-product",
        "connections",
        "location",
        "demographics",
        "companies-followed",
        "groups-joined",
        "education",
        "job-information",
        "employer",
        "websites-visited",
        "ads-beyond-linkedin",
        "actions-that-showed-interest",
        "actions-after-viewing-ads",
    ]
    public_profile = "https://www.linkedin.com/public-profile/settings"  # Record setting
    settings = "https://www.linkedin.com/psettings"


class LoginFieldId:
    user = "session_key"
    pwd = "session_password"
    submit = '//button[@type="submit"]'


class Xpath:
    about = '//section[div[@id="about"]]/div[3]/div/div/div/span[1]'
    checked = "//input[@checked]"
    checked_box = '//div[@class="checkbox-input" and input[@checked]]/label/p'
    checked_switch = '//div[@class="toggle-input" and input[@checked]]/label/p'
    profile = '//a[@href and @class="ember-view block"]'
    public_visibility = '//div[input[@id="toggle-visibilityLevel" and @checked]]/label/span[1]'
    unchecked = "//input[not(@checked)]"


class SecureLI(Securer):
    def __init__(self):
        super().__init__("linkedin")

    def connect(self):
        self.login(Url.main, LoginFieldId.user, LoginFieldId.pwd)
        self.wait_and_click(Xpath.profile, click=False)

    def close(self):
        pause_pre_quit()
        self.cleanup()

    def check_about(self):
        self.driver.find_element(By.XPATH, Xpath.profile).click()
        long_wait()
        summary = self.driver.find_element(By.XPATH, Xpath.about).text
        print(summary)
        if re.search(r"\d{10}", summary) is not None:
            self.log("About/Summary contains your mobile number")

    def public_profile(self):
        id_map = {
            "currentPositions": "currentPositionsDetails",
            "currentPositionsDetails": "currentPositions",
            "pastPositions": "pastPositionsDetails",
            "pastPositionsDetails": "pastPositions",
            "educations": "educationsDetails",
            "educationsDetails": "educations",
        }

        def filter_fields(field_list, checked=True):
            filtered_fields = []
            for field in field_list:
                if "--" in field:
                    field = field.split("--")[1]
                    field = id_map.get(field, field)
                    filtered_fields.append(field)
                elif field.endswith("pictureVisibilityLevel") and checked:
                    field = field.split("-")[0]
                    self.log(f"Picture visibility level is {field}")
            return filtered_fields

        self.driver.get(Url.public_profile)
        short_wait()
        public_profile = self.driver.find_elements(By.XPATH, Xpath.public_visibility)
        if not public_profile:
            self.log("Your profile is private to LinkedIn")
            return 0

        checked_fields = (x.get_attribute("id") for x in self.driver.find_elements(By.XPATH, Xpath.checked))
        unchecked_fields = (x.get_attribute("id") for x in self.driver.find_elements(By.XPATH, Xpath.unchecked))

        self.log(f"OLD:\nVisible in timeline : {filter_fields(checked_fields, checked=True)}")
        self.log(f"Not Visible in timeline : {filter_fields(unchecked_fields, checked=False)}")

        public_profile[0].click()
        self.log("NEW:\nYour profile is set to private")

    def ads(self):
        def uncheck(xpath):
            toggles = self.driver.find_elements(By.XPATH, xpath)
            for toggle in toggles:
                toggle.click()

        self.driver.get(Url.ad_base_url)
        for ad_type in Url.ad_types:
            self.driver.get(f"{Url.ad_base_url}/{ad_type}")
            short_wait()
            uncheck(Xpath.checked_switch)
            uncheck(Xpath.checked_box)
        self.log("All Advertisement data unchecked")

    def secure_all(self):
        steps = [self.connect, self.check_about, self.public_profile, self.ads, self.close]
        for step in steps:
            step()


def main():
    my_linkedin = SecureLI()
    if my_linkedin.username and my_linkedin.password:
        my_linkedin.secure_all()
    else:
        my_linkedin.log("No username/password found")
        my_linkedin.cleanup()


if __name__ == "__main__":
    main()
