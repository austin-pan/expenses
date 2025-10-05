import argparse
import os
import time
import traceback
from typing import List, Tuple

import tqdm
from selenium.common import NoSuchWindowException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support.wait import WebDriverWait

from crawler import crawl

concur_login_url = "https://www.concursolutions.com/"
error_path = "/tmp/expenses_error_screenshot.png"


def parse_transactions(input_dir: str) -> List[Tuple[str, str, str]]:
    """
    Get metadata of each order receipt in `input_dir`. This is done by parsing the
    filenames which are formatted as "{order id}_{date}_{price}.png".
    """
    transactions = []
    for filename in os.listdir(input_dir):
        if filename.endswith(".png"):
            order, date, amount = tuple(filename.rstrip(".png").split("_"))
            date = date.replace("-", "/")
            amount = amount.replace("-", ".")
            transactions.append((filename, date, amount))
    # Sort by dates (year, month, day)
    return sorted(transactions, key=lambda x: crawl.get_comparable_date(x[1], "/"))


def add_expense(driver: WebDriver, input_dir: str, transaction: Tuple[str, str, str]) -> None:
    """
    Fill out an "Add Expense" popup. Fills out date and amount fields and uploads order
    receipt image.

    :param driver: Current web driver
    :param input_dir: Directory where order receipt images are stored
    :param transaction: Transaction metadata as a 3-tuple of order id, date, and price
    :return: None
    """
    (filename, date, amount) = transaction

    transaction_date_field = WebDriverWait(driver, 60).until(lambda d: d.find_element(
        By.CSS_SELECTOR, 'input[data-nuiexp="field-transactionDate"]'
    ))
    crawl.set_field(transaction_date_field, date)

    amount_field = WebDriverWait(driver, 60).until(lambda d: d.find_element(
        By.CSS_SELECTOR, 'input[data-nuiexp="field-transactionAmount"]'
    ))
    crawl.set_field(amount_field, amount)

    add_receipt_button = WebDriverWait(driver, 60).until(lambda d: d.find_element(
        By.CSS_SELECTOR, "button.spend-common__drag-n-drop__button"
    ))
    image_path = os.path.join(input_dir, filename)
    crawl.upload_image(driver, add_receipt_button, image_path)


def add_expenses(driver: WebDriver, input_dir: str) -> None:
    """
    Add all expenses in `input_dir` to expense report. Each order is added as a
    separate "Parking" expense and is added with transaction date, amount, and receipt image.

    :param driver: Current web driver
    :param input_dir: Directory with all order receipts to expense
    :return: None
    """
    transactions = parse_transactions(input_dir)
    for transaction in tqdm.tqdm(transactions):
        def add_expense_button_getter():
            return WebDriverWait(driver, 60).until(lambda d: d.find_element(
                By.XPATH, "//button[contains(., 'Add Expense') and not(@disabled)]"
            ))
        crawl.repeat_click_with_timeout(driver, add_expense_button_getter, 60)

        manual_expense_button = WebDriverWait(driver, 60).until(lambda d: d.find_element(
            By.XPATH, "//button[contains(., 'Manually Create Expense')]"
        ))
        crawl.scroll_and_click_element(driver, manual_expense_button)

        parking_menu_item = WebDriverWait(driver, 60).until(lambda d: d.find_element(
            By.XPATH, "//button[contains(., 'Parking')]"
        ))
        crawl.scroll_and_click_element(driver, parking_menu_item)

        add_expense(driver, input_dir, transaction)
        # Wait for receipt image to load
        WebDriverWait(driver, 60).until(lambda d: d.find_element(
            By.XPATH, "//button[contains(., 'Remove')]"
        ))

        back_to_report_button = WebDriverWait(driver, 60).until(lambda d: d.find_element(
            By.XPATH, "//button[contains(., 'Back to Report')]"
        ))
        crawl.scroll_and_click_element(driver, back_to_report_button)

        save_and_continue_button = WebDriverWait(driver, 60).until(lambda d: d.find_element(
            By.XPATH, "//button[contains(., 'Save & Continue')]"
        ))
        crawl.scroll_and_click_element(driver, save_and_continue_button)


def run(input_dir: str) -> None:
    """
    Create an SAP Concur expense report and add expenses to it.

    :param input_dir: The directory with order receipts to upload to the expense report
    :return: None
    """
    driver = crawl.init_driver()
    try:
        print(f"Navigating to {concur_login_url}...")
        driver.get(concur_login_url)
        print("> Please manually log into SAP Concur...")

        create_button = WebDriverWait(driver, 600).until(lambda d: d.find_element(
            By.XPATH, "//button[contains(., 'Create')]"
        ))
        crawl.scroll_and_click_element(driver, create_button)
        start_report_button = WebDriverWait(driver, 600).until(lambda d: d.find_element(
            By.XPATH, "//a[contains(., 'Start a Report')]"
        ))
        print("Creating expense report...")
        crawl.scroll_and_click_element(driver, start_report_button)
        print("> Please populate expense report creation fields and submit action window...")

        WebDriverWait(driver, 60).until(lambda d: d.find_element(
            By.XPATH, "//button[contains(., 'Add Expense')]"
        ))
        print("Adding expenses...")
        add_expenses(driver, input_dir)

        print("> Expenses successfully added! Close the browser window to exit.")
        while True:
            try:
                # Repeatedly query the current website's title. If the window
                # has been closed, querying the title will throw an exception
                # that gets caught
                _ = driver.title
                time.sleep(1)
            except NoSuchWindowException:
                print("Exiting...")
                break
    except Exception:
        traceback.print_exc()
        driver.save_full_page_screenshot(error_path)
        print(f"Error screenshot saved to {error_path}")
    finally:
        time.sleep(1)
        driver.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create an SAP Concur expense report.")
    parser.add_argument("input", type=str, help="the directory with receipts to upload")
    cmd = parser.parse_args()
    run(os.path.abspath(os.path.expanduser(cmd.input)))
