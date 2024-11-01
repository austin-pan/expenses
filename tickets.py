import argparse
import os
import time
from typing import Any, Callable, Optional, List

from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support.wait import WebDriverWait

from crawler import crawl

caltrain_login_url = "https://caltrain.transitsherpa.com/rider-web/login"
caltrain_orders_url = "https://caltrain.transitsherpa.com/rider-web/account/history"


def traverse_pages(driver: WebDriver, func: Optional[Callable[[Any], bool]] = None, *args, **kwargs) -> int:
    """
    Traverse CalTrain orders pages by clicking on the "Next Page" button. At each page, apply `func`. If `func` returns
    `False`, stop traversing early.

    :param driver: Current web driver
    :param func: Function to apply at each page traversed that returns a `bool`. If `func` returns `False`, stop
    traversing pages early
    :param args: Positional arguments to provide to `func`
    :param kwargs: Keyword arguments to provide to `func`
    :return: Number of pages traversed
    """
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


def save_page_orders(driver: WebDriver, output_dir: str, last_date: Optional[str] = None, parking_prices: List[str] = []) -> bool:
    """
    Take screenshots of each CalTrain order in a page chronologically starting from the latest order until the
    specified date. If `last_date` is not specified or reached in this page, save every CalTrain order of this page.

    :param driver: Current web driver
    :param output_dir: Directory to save screenshots to
    :param last_date: Date to stop saving orders at, exclusive
    :param parking_prices: Valid prices of parking permits
    :return: `True` if `last_date` has not been reached yet, otherwise `False`
    """
    # Hide the footer
    driver.execute_script('arguments[0].style.display="none";', driver.find_element(By.CSS_SELECTOR, "footer"))

    orders_css = "div.ngCanvas > div.ngRow"
    order_elements = WebDriverWait(driver, 60).until(lambda d: d.find_elements(By.CSS_SELECTOR, orders_css))
    orders = []
    for order in order_elements:
        order_num = order.find_element(By.CSS_SELECTOR, "div.col0").text.strip()
        order_date = order.find_element(By.CSS_SELECTOR, "div.col1").text.split()[0].strip()
        order_price = order.find_element(By.CSS_SELECTOR, "div.col2").text.strip().removeprefix("$")
        orders.append((order, (order_num, order_date, order_price)))

    orders.sort(key=lambda x: (crawl.get_comparable_date(x[1][1], "/"), x[1][0]), reverse=True)
    for (order, (order_num, order_date, order_price)) in orders:
        # Last order has been reached, exiting
        if last_date is not None and crawl.get_comparable_date(last_date, "/") >= crawl.get_comparable_date(order_date, "/"):
            return False

        if order_price in parking_prices:
            print(f"Taking screenshot of order(s) on {order_date}...", flush=True, end="\r")
            order_date = order_date.replace("/", "-")
            order_price = order_price.replace(".", "-")
            filename = os.path.join(output_dir, f"{order_num}_{order_date}_{order_price}.png")
            order.screenshot(filename)

    return True


def save_orders(driver: WebDriver, output_dir: str, last_date: Optional[str] = None, parking_prices: List[str] = []) -> None:
    """
    Take screenshots of each CalTrain order chronologically starting from the latest order until the specified date. If
    `last_date` is not specified, save every CalTrain order.

    :param driver: Current web driver
    :param output_dir: Directory to save screenshots to
    :param last_date: Date to stop saving orders at, exclusive
    :param parking_prices: Valid prices of parking permits
    :return: None
    """
    WebDriverWait(driver, 60).until(lambda d: d.find_element(By.CSS_SELECTOR, "div.ngCanvas"))
    traverse_pages(driver, save_page_orders, driver, output_dir, last_date, parking_prices)


def run(output_dir: str, last_date: Optional[str] = None, parking_prices: List[str] = []) -> None:
    """
    Run CalTrain order saving pipeline. Opens CalTrain login page and waits for user to log in. Afterwards, automates
    taking screenshots of each CalTrain order.

    :param output_dir: Directory to save screenshots to
    :param last_date: Date to stop saving orders at, exclusive
    :param parking_prices: Valid prices of parking permits
    :return: None
    """
    driver = crawl.init_driver()

    try:
        print(f"Navigating to {caltrain_login_url}...")
        driver.get(caltrain_login_url)
        WebDriverWait(driver, 600).until(lambda d: d.find_element(By.CSS_SELECTOR, "div.store-logo"))

        print(f"Navigating to {caltrain_orders_url}...")
        driver.get(caltrain_orders_url)
        print("Taking screenshots of order history...")
        save_orders(driver, output_dir, last_date, parking_prices)
    finally:
        time.sleep(1)
        driver.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Take screenshots of CalTrain orders.")
    parser.add_argument("output", type=str, help="the directory to save screenshots to")
    parser.add_argument("-d", "--date", default=None, type=str,
                        help="optional. The date (MM/DD/YYYY) to stop crawling at, exclusive")
    parser.add_argument("-p", "--prices", default=["5.50", "2.75"], type=lambda p: p.split(","),
                        help="optional. Comma-separated list of parking permit prices to restrict to, e.g. `5.50,2.75`")
    cmd = parser.parse_args()
    if cmd.date is not None and cmd.date.count("/") != 2:
        # Very poor way to check date format lol
        raise ValueError("Date must be in MM/DD/YYYY format.")
    run(os.path.abspath(os.path.expanduser(cmd.output)), cmd.date, cmd.prices)
