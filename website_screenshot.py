# Description: this is a python script that uses Selenium to take a screenshot of a website

# import libraries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# from selenium.webdriver.chrome.service import Service
import time
from PIL import Image
import io
import base64
from datetime import date
import re
import os

# configure options
options = Options()
options.headless = True
options.add_argument("--window-size=1280,1024")
# options.add_argument("--window-size=3000,3000")
# driverpath = Service('/Users/clairebesset/2024-code/chromedriver_mac64/chromedriver') #add your own path
# driver = webdriver.Chrome(service=driverpath, options=options)


def create_target_folder(
    target_folder_name,
):  # returns target folder path and creates it if it doesn't exist
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.realpath(__file__))
    # Create a path to the target folder
    output_dir = os.path.join(script_dir, target_folder_name)
    # check if target folder exists and create it if it doesn't
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return output_dir


def sanitize_url(url):  # returns sanitized url for filename
    url = url.replace("https://", "").replace("http://", "")  # Remove http/https
    url = re.sub(r'[\\/*?:"<>|]', "", url)  # Remove invalid characters
    url = url.replace(".", "_")  # Replace dots with underscores
    return url


def create_fullpath_from_url(
    url, filename_qualifier, target_folder, extension, domain_only=False
):  # returns filename containing url and current date
    # create string with current date in format YYYY-MM-DD
    today = date.today()
    datestring = today.strftime("%Y-%m-%d")
    if domain_only:
        # get domain name
        url = url.split("//")[-1].split("/")[0]
    url = sanitize_url(url)
    # create filename containing url and current date
    filename = datestring + url + filename_qualifier + extension
    # create path to target folder
    fullpath = os.path.join(target_folder, filename)
    return fullpath


def open_browser():  # open Chrome browser, returns driver
    # Create a new instance of the Chrome driver
    driver = webdriver.Chrome(options=options)
    return driver


def get_url(driver, url, time_to_wait):  # returns driver
    # Go to the page that we want to scrape
    driver.get(url)
    # Wait for the page to load
    time.sleep(time_to_wait)  # Adjust this number as needed
    return driver


def scroll_to_bottom_slowly(
    driver,
):  # scrolls to bottom of page slowly to load all content
    # Get scroll height
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll down to bottom slowly
        scroll_height = driver.execute_script("return document.body.scrollHeight;")
        steps = 10  # Increase or decrease this value as needed
        step_size = scroll_height / steps

        for i in range(steps):
            driver.execute_script(f"window.scrollTo(0, {step_size * (i + 1)});")
            time.sleep(0.5)  # Increase or decrease this value as needed

        # Wait to load page
        time.sleep(2)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    return driver


def take_screenshot(
    driver, filename
):  # saves png to current folder ### THIS ONLY TAKES AN "ABOVE-THE-FOLD" SCREENSHOT
    # Get the width and height of the page
    scroll_width = driver.execute_script("return document.body.parentNode.scrollWidth")
    scroll_height = driver.execute_script(
        "return document.body.parentNode.scrollHeight"
    )
    print(scroll_width, scroll_height)
    driver.set_window_size(
        scroll_width, scroll_height
    )  ## I wasn't able to get this to work
    # Take screenshot
    driver.save_screenshot(filename)
    return


def capture_full_page_screenshot(
    driver, filename
):  # saves png to current folder ### THIS TAKES A FULL PAGE SCREENSHOT
    # Get screenshot as base64
    screenshot_base64 = driver.execute_cdp_cmd(
        "Page.captureScreenshot", {"format": "png", "captureBeyondViewport": True}
    )["data"]
    # Convert base64 to bytes
    screenshot_bytes = base64.b64decode(screenshot_base64)
    # Open bytes as an image
    image = Image.open(io.BytesIO(screenshot_bytes))
    # Save image as PNG
    image.save(filename)


def quit_browser(driver):  # quit browser
    driver.quit()
    return


def open_screenshot(filename):  # opens screenshot
    image = Image.open(filename)
    image.show()
    return


target_folder = "saved screenshots"
filename_qualifier = "_screenshot"
filename_domain_only = False
extension = ".png"
target_folder = create_target_folder(target_folder)


# url to take screenshot of
urls = ["https://poly.ai/", "https://www.google.com/"]
time_to_wait = 1

# open browser
driver = open_browser()

for url in urls: 
    fullpath = create_fullpath_from_url(
        url, filename_qualifier, target_folder, extension, filename_domain_only
    )
    driver = get_url(driver, url, time_to_wait)
    driver = scroll_to_bottom_slowly(driver)
    # take screenshot
    capture_full_page_screenshot(driver, fullpath)
    # open screenshot
    # open_screenshot(fullpath)
# quit browser
quit_browser(driver)

