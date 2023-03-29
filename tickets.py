import argparse
import os
import time
from typing import Any, Callable, Optional

from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support.wait import WebDriverWait

from crawler import crawl

caltrain_login_url = "https://caltrain.transitsherpa.com/rider-web/login"
caltrain_orders_url = "https://caltrain.transitsherpa.com/rider-web/account/history"


def traverse_pages(driver: WebDriver, func: Optional[Callable[[Any], bool]] = None, *args, **kwargs) -> int:
    num_pages = 0
    while True:
        num_pages += 1
        if func is not None:
            continue_traversing = func(*args, **kwargs)
            if not continue_traversing:
                break

        try:
            # When last page is reached, the next button is disabled
            driver.find_element(By.CSS_SELECTOR, 'button[title="Next Page"][disabled="disabled"]')
            break
        except NoSuchElementException:
            pass

        # Click next page button
        next_page_button = WebDriverWait(driver, 60).until(lambda d: d.find_element(By.CSS_SELECTOR, 'button[title="Next Page"]'))
        crawl.scroll_and_click_element(driver, next_page_button)

    return num_pages


def save_page_orders(driver: WebDriver, output_dir: str, last_date: Optional[str] = None) -> bool:
    # Hide the footer
    driver.execute_script('arguments[0].style.display="none";', driver.find_element(By.CSS_SELECTOR, "footer"))

    orders_css = "div.ngCanvas > div.ngRow"
    order_elements = WebDriverWait(driver, 60).until(lambda d: d.find_elements(By.CSS_SELECTOR, orders_css))
    orders = []
    for order in order_elements:
        order_num = order.find_element(By.CSS_SELECTOR, "div.col0").text.strip()
        order_date = order.find_element(By.CSS_SELECTOR, "div.col1").text.split()[0].strip()
        order_price = order.find_element(By.CSS_SELECTOR, "div.col2").text.replace(".", "-").strip().removeprefix("$")
        orders.append((order, (order_num, order_date, order_price)))

    orders.sort(key=lambda x: (crawl.get_comparable_date(x[1][1], "/"), x[1][0]), reverse=True)
    for (order, (order_num, order_date, order_price)) in orders:
        # Last order has been reached, exiting
        if last_date is not None and crawl.get_comparable_date(last_date, "/") >= crawl.get_comparable_date(order_date, "/"):
            return False

        print(f"Taking screenshot of order(s) on {order_date}...", flush=True, end="\r")
        order_date = order_date.replace("/", "-")
        filename = os.path.join(output_dir, f"{order_num}_{order_date}_{order_price}.png")
        order.screenshot(filename)

    return True


def save_orders(driver: WebDriver, output_dir: str, last_date: Optional[str] = None) -> None:
    WebDriverWait(driver, 60).until(lambda d: d.find_element(By.CSS_SELECTOR, "div.ngCanvas"))
    traverse_pages(driver, save_page_orders, driver, output_dir, last_date)


def run(output_dir: str, last_date: Optional[str] = None):
    driver = crawl.init_driver()

    try:
        print(f"Navigating to {caltrain_login_url}...")
        driver.get(caltrain_login_url)
        WebDriverWait(driver, 600).until(lambda d: d.find_element(By.CSS_SELECTOR, "div.store-logo"))

        print(f"Navigating to {caltrain_orders_url}...")
        driver.get(caltrain_orders_url)
        print("Taking screenshots of order history...")
        save_orders(driver, output_dir, last_date)
    finally:
        time.sleep(1)
        driver.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Take screenshots of CalTrain orders.")
    parser.add_argument("-o", "--output", required=True, type=str, help="the directory to save screenshots to")
    parser.add_argument("-d", "--date", default=None, type=str,
                        help="optional. The date (MM/DD/YYYY) to stop crawling at, exclusive")
    cmd = parser.parse_args()
    if cmd.date is not None and cmd.date.count("/") != 2:
        # Very poor way to check date format lol
        raise ValueError("Date must be in MM/DD/YYYY format.")
    run(os.path.expanduser(cmd.output), cmd.date)
