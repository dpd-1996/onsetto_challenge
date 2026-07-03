from .base_page import BasePage
from utils.data_factory import AccountDetails, CardDetails
from playwright.sync_api import expect

class AccountPage(BasePage):

    #Bank Details locators
    BANK_ROUTING_INPUT = "bank-routing"
    BANK_ACCOUNT_INPUT = "bank-account"
    BANK_SAVE_BUTTON = "bank-save"
    BANK_SAVED_INFO = "bank-saved-info"

    BANK_ROUTING_ERROR = "//div[contains(text(),'Routing number must be exactly 9 digits')]"
    BANK_ACCOUNT_ERROR = "//div[contains(text(),'Account number must be 4 to 17 digits')]"
    BANK_DETAILS_SAVED = "//div[contains(text(),'Banking details saved')]"

    #Card Details locators
    CARD_HOLDER_INPUT = "card-holder"
    CARD_NUMBER_INPUT = "card-number"
    CARD_EXP_MONTH_INPUT = "card-exp-month"
    CARD_EXP_YEAR_INPUT = "card-exp-year"
    CARD_CVC_INPUT = "card-cvc"
    CARD_SAVE_BUTTON = "card-save"
    CARD_SAVED_INFO = "payment-saved-info"

    CARD_NUMBER_ERROR = "//div[contains(text(),'Invalid card number (Luhn check failed)')]"
    CARD_EXP_ERROR = "//div[contains(text(),'Expiration must be in the future')]"
    ERROR_SECTION= "//section[@aria-label='Notifications alt+T']"
    ERROR_LOCATOR = "//li/div[2]"

    def navigate_to_account_page(self):
        try:
            self.page.get_by_role("link", name="Account").click()
        except Exception as e:
            print(f"Error occurred while navigating to account page: {e}")  
        
    def fill_bank_details(self, details: AccountDetails):
        self.page.get_by_test_id(self.BANK_ROUTING_INPUT).fill(details.routing_number)
        self.page.get_by_test_id(self.BANK_ACCOUNT_INPUT).fill(details.account_number)
        return self  # Return self to allow method chaining
    

    def save_bank_details(self, details: AccountDetails):
        self.fill_bank_details(details)
        self.page.get_by_test_id(self.BANK_SAVE_BUTTON).click()
        return self
    
    def banking_summary(self):
        text = self.page.get_by_test_id(self.BANK_SAVED_INFO).inner_text().strip()
        return text

    # ---Payment Card Details Methods---

    def fill_card_details(self, details: CardDetails):
        self.page.get_by_test_id(self.CARD_HOLDER_INPUT).fill(details.holder_name)
        self.page.get_by_test_id(self.CARD_NUMBER_INPUT).fill(details.card_number)
        self.page.get_by_test_id(self.CARD_EXP_MONTH_INPUT).fill(details.exp_month)
        self.page.get_by_test_id(self.CARD_EXP_YEAR_INPUT).fill(details.exp_year)
        self.page.get_by_test_id(self.CARD_CVC_INPUT).fill(details.cvc)
        return self

    def save_card_details(self, details: CardDetails):
        self.fill_card_details(details)
        self.page.get_by_test_id(self.CARD_SAVE_BUTTON).click()
        return self
    
    def payment_summary(self):
        text = self.page.get_by_test_id(self.CARD_SAVED_INFO).inner_text().strip()
        return text
    
    def get_error_messages(self,):
        section = self.page.locator(self.ERROR_SECTION)
        locator = section.locator(self.ERROR_LOCATOR).first
        return locator.inner_text()