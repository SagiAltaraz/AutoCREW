import pytest
from playwright.sync_api import Page, expect


BASE_URL = "http://localhost:3000"


def test_page_loads(page: Page):
    page.goto(BASE_URL)
    expect(page).to_have_title("AutoCrew — AI Research Platform")


def test_task_input_visible(page: Page):
    page.goto(BASE_URL)
    expect(page.locator("textarea")).to_be_visible()
    expect(page.get_by_role("button", name="Launch Crew")).to_be_visible()


def test_agent_cards_visible(page: Page):
    page.goto(BASE_URL)
    for label in ["Manager", "Research", "Analyst", "Writer"]:
        expect(page.get_by_text(label)).to_be_visible()


def test_example_prompt_clickable(page: Page):
    page.goto(BASE_URL)
    page.get_by_text("Research Tesla Q4 2024 performance").click()
    expect(page.locator("textarea")).to_have_value("Research Tesla Q4 2024 performance")


def test_submit_disabled_when_empty(page: Page):
    page.goto(BASE_URL)
    page.locator("textarea").fill("")
    expect(page.get_by_role("button", name="Launch Crew")).to_be_disabled()


def test_submit_shows_loading(page: Page):
    page.goto(BASE_URL)
    page.locator("textarea").fill("Test research topic")
    page.get_by_role("button", name="Launch Crew").click()
    expect(page.locator("[data-testid='spinner']")).to_be_visible(timeout=3000)
