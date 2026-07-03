"""Base page class for Playwright tests with shared helpers"""
from playwright.sync_api import sync_playwright

class BasePage:
    def __init__(self, page):
        self.page = page

    def goto(self, url):
        self.page.goto(url)
        return self

    def text_of(self, selector):
        return (self.page.locator(selector).inner_text() or "").strip()
