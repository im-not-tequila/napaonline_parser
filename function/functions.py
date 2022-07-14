import time
import bs4

import undetected_chromedriver as webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from .settings import Settings


def get_web_page_selenium(driver, link: str, dop_sleep=0) -> str:
    page_str: str = ''

    while page_str == '':
        try:
            driver.execute_script("window.stop();")
            driver.set_page_load_timeout(15)
            driver.get(link)
            time.sleep(dop_sleep)
        except TimeoutException:
            driver.execute_script("window.stop();")
            # page_str = driver.page_source
            page_str = driver.execute_script("return document.body.innerHTML;")

            if page_str == '<html><head></head><body></body></html>':
                get_web_page_selenium(driver, link)

            return page_str
        except Exception as e:
            continue

        # page_str = driver.page_source
        page_str = driver.execute_script("return document.body.innerHTML;")

        if page_str == '<html><head></head><body></body></html>':
            get_web_page_selenium(driver, link)

    return page_str


def skip_cloudflare(link: str) -> webdriver:
    options = webdriver.options.ChromeOptions()

    if not Settings.HEADLESS:
        options.add_argument("--headless")

    # options.add_argument("start-maximized")
    # options.add_argument("enable-automation")
    # options.add_argument("--no-sandbox")
    # options.add_argument("--disable-dev-shm-usage")
    # options.add_argument("--disable-browser-side-navigation")
    # options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(10)
    driver.get(link)

    try:
        while bs4.BeautifulSoup(driver.page_source, 'html.parser').find('title').text == 'Please Wait... | Cloudflare':
            pass
    except TimeoutException:
        pass
    except WebDriverException:
        pass

    if bs4.BeautifulSoup(driver.page_source, 'html.parser').find('title').text == 'Please Wait... | Cloudflare':
        driver.quit()
        skip_cloudflare(link)
    else:
        return driver
