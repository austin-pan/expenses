import argparse
import os
import time
from typing import List, Tuple

from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support.wait import WebDriverWait
import tqdm

from crawler import crawl

concur_login_url = "https://www.concursolutions.com/"


def start_report(driver: WebDriver):
    start_report_button = WebDriverWait(driver, 60).until(lambda d: d.find_element(By.LINK_TEXT, "Start a Report"))
    crawl.scroll_and_click_element(driver, start_report_button)

    walkthru_button = WebDriverWait(driver, 60).until(lambda d: d.find_element(By.CSS_SELECTOR, "span.walkme-custom-balloon-button-text"))
    crawl.scroll_and_click_element(driver, walkthru_button)

    report_name_field = WebDriverWait(driver, 60).until(lambda d: d.find_element(By.CSS_SELECTOR, "input#name"))
    crawl.set_field(report_name_field, "Palo Alto CalTrain Parking")
    report_name_field.submit()


def process_transactions(input_dir: str) -> List[Tuple[str, str, str]]:
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


def add_expense(driver: WebDriver, input_dir: str, transaction: Tuple[str, str, str]):
    (filename, date, amount) = transaction

    transaction_date_field = WebDriverWait(driver, 60).until(lambda d: d.find_element(By.CSS_SELECTOR, 'input[name="transactionDate"]'))
    crawl.set_field(transaction_date_field, date)

    amount_field = WebDriverWait(driver, 60).until(lambda d: d.find_element(By.CSS_SELECTOR, 'input[name="transactionAmount"]'))
    crawl.set_field(amount_field, amount)

    add_receipt_button = WebDriverWait(driver, 60).until(lambda d: d.find_element(By.CSS_SELECTOR, "button.spend-common__drag-n-drop__button"))
    image_path = os.path.join(input_dir, filename)
    crawl.upload_image(driver, add_receipt_button, image_path)


def add_expenses(driver: WebDriver, input_dir: str):
    transactions = process_transactions(input_dir)
    for transaction in tqdm.tqdm(transactions):
        add_expense_button = WebDriverWait(driver, 60).until(lambda d: d.find_element(By.CSS_SELECTOR, 'span[data-trans-id="Expense.addExpense"]'))
        crawl.scroll_and_click_element(driver, add_expense_button)

        parking_menu_item = WebDriverWait(driver, 60).until(lambda d: d.find_element(By.CSS_SELECTOR, 'button.menu-category-item__button[data-nuiexp="TRANS-listItem-Parking"]'))
        crawl.scroll_and_click_element(driver, parking_menu_item)

        add_expense(driver, input_dir, transaction)
        # Wait for receipt image to load
        WebDriverWait(driver, 60).until(lambda d: d.find_element(By.CSS_SELECTOR, 'button[title="Remove Receipt"]'))

        save_expense_button = WebDriverWait(driver, 60).until(lambda d: d.find_element(By.CSS_SELECTOR, 'span[data-trans-id="expenseEntry.saveExpense"]'))
        crawl.scroll_and_click_element(driver, save_expense_button)


def run(input_dir: str):
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

        WebDriverWait(driver, 60).until(lambda d: d.find_element(By.CSS_SELECTOR, 'button[data-nuiexp="reportActionButtons.submitButton"]'))
        WebDriverWait(driver, 3600).until_not(lambda d: d.find_element(By.CSS_SELECTOR, 'button[data-nuiexp="reportActionButtons.submitButton"]'))
    finally:
        time.sleep(1)
        driver.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="create an SAP Concur expense report")
    parser.add_argument("-i", "--input", required=True, type=str, help="the directory with receipts to upload")
    cmd = parser.parse_args()
    run(os.path.expanduser(cmd.input))
