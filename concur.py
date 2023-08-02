import argparse
import os
import time
from typing import List, Tuple

from selenium.common import ElementNotInteractableException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support.wait import WebDriverWait
import tqdm

from crawler import crawl

concur_login_url = "https://www.concursolutions.com/"


def start_report(driver: WebDriver) -> None:
    """
    Start an SAP Concur expense report.
    """
    start_report_button = WebDriverWait(driver, 60).until(lambda d: d.find_element(By.LINK_TEXT, "Start a Report"))
    crawl.scroll_and_click_element(driver, start_report_button)

    # Skip walk-through if prompted
    try:
        walkthru_button = WebDriverWait(driver, 5).until(lambda d: d.find_element(By.CSS_SELECTOR, "span.walkme-custom-balloon-button-text"))
        crawl.scroll_and_click_element(driver, walkthru_button)
    except TimeoutException:
        pass

    # Skip tour
    try:
        notification_cancel_button = WebDriverWait(driver, 5).until(lambda d: d.find_element(By.CSS_SELECTOR, "button.notification_cancel"))
        crawl.scroll_and_click_element(driver, notification_cancel_button)
    except TimeoutException:
        pass

    # Set report name
    report_name_field = WebDriverWait(driver, 60).until(lambda d: d.find_element(By.CSS_SELECTOR, "input#name"))
    crawl.set_field(report_name_field, "Palo Alto CalTrain Parking")
    report_name_field.submit()


def process_transactions(input_dir: str) -> List[Tuple[str, str, str]]:
    """
    Get metadata of each order receipt in `input_dir`. This is done by parsing the filenames which are formatted as
    "{order id}_{date}_{price}.png".
    """
    transactions = []
    for filename in os.listdir(input_dir):
        if filename == ".DS_Store":
            continue
        order, date, amount = tuple(filename.rstrip(".png").split("_"))
        date = date.replace("-", "/")
        amount = amount.replace("-", ".")
        transactions.append((filename, date, amount))
    # Sort by dates (year, month, day)
    return sorted(transactions, key=lambda x: crawl.get_comparable_date(x[1], "/"))


def add_expense(driver: WebDriver, input_dir: str, transaction: Tuple[str, str, str]) -> None:
    """
    Fill out an "Add Expense" popup. Fills out date and amount fields and uploads order receipt image.

    :param driver: Current web driver
    :param input_dir: Directory where order receipt images are stored
    :param transaction: Transaction metadata as a 3-tuple of order id, date, and price
    :return: None
    """
    (filename, date, amount) = transaction

    transaction_date_field = WebDriverWait(driver, 60).until(lambda d: d.find_element(By.CSS_SELECTOR, 'input[data-nuiexp="field-transactionDate"]'))
    crawl.set_field(transaction_date_field, date)

    amount_field = WebDriverWait(driver, 60).until(lambda d: d.find_element(By.CSS_SELECTOR, 'input[data-nuiexp="field-transactionAmount"]'))
    crawl.set_field(amount_field, amount)

    add_receipt_button = WebDriverWait(driver, 60).until(lambda d: d.find_element(By.CSS_SELECTOR, "button.spend-common__drag-n-drop__button"))
    image_path = os.path.join(input_dir, filename)
    crawl.upload_image(driver, add_receipt_button, image_path)


def add_expenses(driver: WebDriver, input_dir: str) -> None:
    """
    Add all expenses in `input_dir` to expense report. Each order is added as a separate "Parking" expense and is added
    with transaction date, amount, and receipt image.

    :param driver: Current web driver
    :param input_dir: Directory with all order receipts to expense
    :return: None
    """
    transactions = process_transactions(input_dir)
    for transaction in tqdm.tqdm(transactions):
        add_expense_button = WebDriverWait(driver, 60).until(lambda d: d.find_element(By.CSS_SELECTOR, 'span[data-trans-id="Expense.addExpense"]'))
        crawl.scroll_and_click_element(driver, add_expense_button)

        parking_menu_item = WebDriverWait(driver, 60).until(lambda d: d.find_element(By.CSS_SELECTOR, 'button.menu-category-item__button[data-nuiexp="TRANS-listItem-Parking"]'))
        crawl.scroll_and_click_element(driver, parking_menu_item)

        add_expense(driver, input_dir, transaction)
        # Wait for receipt image to load
        WebDriverWait(driver, 60).until(lambda d: d.find_element(By.CSS_SELECTOR, 'button[data-nuiexp="receipt-viewer__detach"]'))

        save_expense_button = WebDriverWait(driver, 60).until(lambda d: d.find_element(By.CSS_SELECTOR, 'button[data-nuiexp="save-expense"]'))
        crawl.scroll_and_click_element(driver, save_expense_button)


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
        WebDriverWait(driver, 600).until(lambda d: d.find_element(By.LINK_TEXT, "Start a Report"))
        print(f"Creating expense report...")
        start_report(driver)
        WebDriverWait(driver, 60).until(lambda d: d.find_element(By.CSS_SELECTOR, 'span[data-trans-id="Expense.addExpense"]'))
        print(f"Adding expenses...")
        add_expenses(driver, input_dir)

        input("Press ENTER to exit: ")
    except ElementNotInteractableException as e:
        print(str(e))
        error_path = "/tmp/expenses_error_screenshot.png"
        driver.save_full_page_screenshot(error_path)
        print(f"Error screenshot saved to {error_path}")
    finally:
        time.sleep(1)
        driver.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create an SAP Concur expense report.")
    parser.add_argument("input", type=str, help="the directory with receipts to upload")
    cmd = parser.parse_args()
    run(os.path.expanduser(cmd.input))
