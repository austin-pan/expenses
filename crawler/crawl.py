from selenium import webdriver
from selenium.common import ElementClickInterceptedException
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait

# Copied from https://sqa.stackexchange.com/a/22199
# Javascript for creating a custom element for uploading an image into, and then dragging and dropping that uploaded
# image to into a specified element.
_js_drop_file = """
var target = arguments[0],
    offsetX = arguments[1],
    offsetY = arguments[2],
    document = target.ownerDocument || document,
    window = document.defaultView || window;

var input = document.createElement('INPUT');
input.type = 'file';
input.style.display = 'none';
input.onchange = function () {
    var rect = target.getBoundingClientRect(),
    x = rect.left + (offsetX || (rect.width >> 1)),
    y = rect.top + (offsetY || (rect.height >> 1)),
    dataTransfer = { files: this.files };

    ['dragenter', 'dragover', 'drop'].forEach(function (name) {
        var evt = document.createEvent('MouseEvent');
        evt.initMouseEvent(name, !0, !0, window, 0, 0, 0, x, y, !1, !1, !1, !1, 0, null);
        evt.dataTransfer = dataTransfer;
        target.dispatchEvent(evt);
    });
    setTimeout(function () { document.body.removeChild(input); }, 25);
};
document.body.appendChild(input);
return input;
"""


def upload_image(driver: WebDriver, element: WebElement, filepath: str) -> None:
    """
    Upload an image into the specified element.

    :param driver: Current web driver
    :param element: Element to upload image into
    :param filepath: Image to upload
    :return: None
    """
    # Drag images into upload files element
    upload = driver.execute_script(_js_drop_file, element, 0, 0)
    upload.send_keys(filepath)


def get_comparable_date(date: str, sep: str) -> list[str]:
    """
    Returns date parts sorted in YYYY-MM-DD which are chronologically comparable.

    :param date: Date to convert
    :param sep: Date part separator
    :return: Date parts in YYYY-MM-DD order
    """
    date_parts = date.split(sep)
    # [YYYY, MM, DD]
    return [date_parts[date_part] for date_part in [2, 0, 1]]


def scroll_and_click_element(driver: WebDriver, element: WebElement) -> None:
    """
    Wait until element is clicked successfully.
    """
    WebDriverWait(driver, 60).until(lambda _: successful_click(element))


def successful_click(element: WebElement) -> bool:
    """
    Scroll to element and click it.
    """
    try:
        # noinspection PyStatementEffect
        element.location_once_scrolled_into_view
        element.click()
        return True
    except ElementClickInterceptedException:
        return False


def set_field(element: WebElement, *value) -> None:
    """
    Set the value of an element by clearing the element and then sending keystrokes.
    """
    element.clear()
    element.send_keys(*value)


def init_driver(*args) -> WebDriver:
    """
    Initialize a remote controlled Firefox browser instance and return its web driver.

    :param args: The arguments to pass to the Firefox web driver, e.g. "--headless"
    :return: Firefox web driver
    """
    firefox_options = webdriver.FirefoxOptions()
    for arg in args:
        firefox_options.add_argument(arg)
    return webdriver.Firefox(options=firefox_options)
