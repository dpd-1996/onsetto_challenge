from .base_page import BasePage
from playwright.sync_api import expect


class LoginPage(BasePage):
    LOGIN_BUTTON = "Log in"
    USERNAME = "#email"
    PASSWORD = "#password"
    SUBMIT_BUTTON = "Sign in"

    #----MFA page locators----
    MFA_HEADER = "Verify your identity"
    VERIFY = "Verify"

    def navigate(self):
        return self.page.get_by_role("button", name=self.LOGIN_BUTTON).first.click()


    def login(self, username: str, password: str):
        self.page.locator(self.USERNAME).fill(username)
        self.page.locator(self.PASSWORD).fill(password)
        self.page.get_by_role("button", name=self.SUBMIT_BUTTON).click()
        self.page.wait_for_load_state("networkidle")
        mfa_heading = self.page.get_by_role("heading", name=self.MFA_HEADER)
        expect(mfa_heading).to_be_visible(timeout=4000)
        return self
    

    def submit_code(self, code: str):
        self.page.get_by_role("textbox").fill(code)
        self.page.get_by_role("button", name=self.VERIFY).click()
        # Land on the authenticated app before storage state is captured.
        self.page.wait_for_url("**/app/**")
        return self