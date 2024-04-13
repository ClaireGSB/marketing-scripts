# Import libraries
import os
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
import json
import time
import pprint
import pandas as pd

# import gspread
from datetime import date
import re


def open_browser():  # returns driver
    # Create a new instance of the Firefox driver
    driver = webdriver.Firefox()
    return driver


def get_url_html(driver, url):  # returns html of the url as a soup object
    # Go to the page that we want to scrape
    driver.get(url)
    # Wait for the page to load
    time.sleep(4)  # Adjust this number as needed
    # Parse the HTML with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, "html.parser")
    return soup


def quit_browser(driver):  # quits the browser
    driver.quit()
    return


# There are 2 possible methods to extract a table content
def get_content_from_divs_looking_like_tables(soup): 
    # Find all divs in the page
    divs = soup.find_all("div")

    # Filter out divs that don't contain at least a certain number of other divs
    min_divs = 7  # Adjust this number as needed
    div_tables = [
        div for div in divs if len(div.find_all("div", recursive=False)) >= min_divs
    ]

    # Now div_tables contains all divs that look like tables
    print("Number of divs that look like tables: ", len(div_tables))

    def find_innermost_divs(div):
        child_divs = div.find_all("div", recursive=False)
        if not child_divs:
            return [div]
        else:
            return [
                innermost_div
                for child_div in child_divs
                for innermost_div in find_innermost_divs(child_div)
            ]

    # Use the function on each div that looks like a table
    item_list = []
    for div in div_tables:
        innermost_divs = find_innermost_divs(div)
        for innermost_div in innermost_divs:
            # print text but if the text is contained in different html elements (e.g. <p> or <a> or <button>), add a space when moving to next element and remove any line breaks
            print(innermost_div.get_text(separator=" ").replace("\n", " ").strip())
            item_info = []
            # add each text element to the item info list
            for text_element in innermost_div.find_all(text=True):
                # only add text elements that contains at least one letter
                if any(c.isalpha() for c in text_element):
                    item_info.append(text_element.strip())
            # add the item info list to the item list
            item_list.append(item_info)
    return item_list


def get_content_from_div_class(soup, item_class, getText= True, getLinks = True, getImages = True): 
    # Find all divs in the page with the class that contains targeted items
    items = soup.find_all(class_=item_class)
    print("Number of items: ", len(items))
    item_list = []
    # add each item to the dictionary
    for item in items:
        item_info = []
        if getText:
        # add each text element to the speaker info list
            for text_element in item.find_all(text=True):
                # only add text elements that contains at least one letter
                if any(c.isalpha() for c in text_element):
                    item_info.append(text_element.strip())
        if getLinks:
            #also get all links
            for link in item.find_all('a', href=True):
                item_info.append(link['href'])
        if getImages:
            #also get all images
            for img in item.find_all('img', src=True):
                item_info.append(img['src'])
        # add the speaker info list to the speaker list
        item_list.append(item_info)
    return item_list


# Functions to process speaker list
def create_item_list_data_frame(item_list):  # returns item list as a dataframe
    # Set pandas options
    pd.set_option("display.max_colwidth", None)
    pd.set_option("display.max_rows", None)
    # pd.set_option('display.max_columns', None)
    # Create a DataFrame
    df = pd.DataFrame(item_list)
    return df


def create_target_folder(target_folder_name):  # returns target folder path and creates it if it doesn't exist
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
    url, filename_qualifier, target_folder, extension, domain_only = False
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


def save_dataframe_to_csv(
    df, csv_fullpath
):  # saves dataframe to csv - arguments: dataframe, csv file name
    # display data as a csv
    df.to_csv(csv_fullpath, index=False)
    return


def open_csv_file(csv_file_name):  # opens csv file in default application
    os.system("open " + csv_file_name)
    return


def print_dataframe(df):  # prints dataframe in terminal
    print(df)
    return


def create_google_sheet():  # returns sheet object (sh)
    gc = gspread.oauth(
        credentials_filename="client_secret_929638313565-p281a3j996igs3kmro4le8s4i009306k.apps.googleusercontent.com.json"
    )
    # gc = gspread.oauth()
    # create google sheet name
    google_sheet_name = "Speaker_List_Spreadsheet_" + time.strftime("%Y%m%d")
    sh = gc.create(google_sheet_name)
    # open the sheet
    sh = gc.open(google_sheet_name)
    return sh


def send_dataframe_to_new_google_sheet_tab(
    df, sh, speaker_list_name
):  # creates new tab in open sheet (sh) and sends dataframe to it. returns worksheet url
    # create a new sheet tab
    sh.add_worksheet(title=speaker_list_name, rows="1000", cols="20")
    # select recently created sheet
    worksheet = sh.worksheet(speaker_list_name)
    # update the sheet with the dataframe
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())
    # get link of the sheet
    sheet_url = sh.url
    # get link of the worksheet
    worksheet_url = worksheet.url
    return worksheet_url


def open_google_sheet(worksheet_url):  # opens google sheet in web browser
    import webbrowser

    webbrowser.open(worksheet_url)
    return


####2 methods possible: let the program identify table automatically (method 1)
#### or provide the class of the div containing the item info (method 2)
### if using method 1, no need to provide item_class, the second element of the tuple in the urls list (can leave it empty)
urls = [
    (
        "https://newyork.theaisummit.com/sponsors-exhibitors",
        "m-libraries-sponsors-list__items__item__image",
    ),
    (
        "https://reg.summit.snowflake.com/flow/snowflake/summit24/speakers/page/catalog",
        "attendee-tile-text-container",
    ),
]
target_folder = "speaker_lists"
filename_qualifier = "speaker_list"
extension = ".csv"
target_folder = create_target_folder(target_folder)
# Specify what to get from the html
getText= True
getLinks = True
getImages = True


driver = open_browser()
for url in urls:
    # print getting url
    print(url[0])
    soup = get_url_html(driver, url[0])
    ###### Get speaker list from html
    ### using method 1
    # speaker_list = get_content_from_divs_looking_like_tables(soup)
    ### using method 2 
    item_class = url[1]
    item_list = get_content_from_div_class(soup, item_class, getText, getLinks, getImages)
    ##### end of getting speaker list from html
    df = create_item_list_data_frame(item_list)
    # filename = create_speaker_list_name(url[0])
    fullpath = create_fullpath_from_url(url[0], filename_qualifier, target_folder, extension, domain_only=True)
    save_dataframe_to_csv(df, fullpath)
    open_csv_file(fullpath)
    # print_dataframe(df)
quit_browser(driver)
