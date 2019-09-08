import os
import time
from datetime import date
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

import parse_url
from config import COUNTIES, URL_FOLDER, PROJ_ROOT

def crall_county(county, today_str):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.binary_location = '/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary'

    driver = webdriver.Chrome(executable_path=os.path.abspath("chromedriver"), chrome_options=chrome_options)
    driver.get("http://www.auction.com")

    county_str = '{} County, CA'.format(county)
    print('working on {}'.format(county_str))
    search_field = driver.find_element_by_name("Search")

    search_field.clear()
    search_field.send_keys(county_str)
    search_field.send_keys(Keys.RETURN)
    time.sleep(10)
    driver.save_screenshot('/tmp/{}.png'.format(county_str))
    # pagination starts from 1
    i = 1
    while True:
        fname = os.path.join(PROJ_ROOT, URL_FOLDER, '{}_{}_{}.html'.format(today_str, county, i))
        with open(fname, 'w+t') as fid:
            print(i, len(driver.page_source))
            fid.write(driver.page_source)

        try:
            i += 1
            next_button = driver.find_element_by_link_text(str(i))
            next_button.click()
        except:
            break

    driver.close()


def find_finder(driver, attr):
    """
    Just a tool to try to find which driver method will find string 'attr'

    :param driver:
    :param attr:
    :return:
    """
    finders = [f for f in driver.__dir__() if f.startswith('find_element_')]
    for finder in finders:
        try:
            element = getattr(driver, finder)(attr)
            print(finder)
        except:
            continue


def crall_all_counties():
    """
    Wrapper to call crall_county on each County in config.COUNTIES
    It also prints how many properties it found per county at the end
    :return:
    """
    today_str = date.today().strftime('%Y%m%d')
    """
    for county in COUNTIES:
        crall_county(county, today_str)
    """

    # Get active auctions in 'files' to 'active_auctions_df'
    wildcard = '{}_*.html'.format(today_str)
    active_auctions_df = parse_url.process_html_files(wildcard, today_str)
    if not active_auctions_df.empty:
        print(active_auctions_df.groupby('county').count()['city'])
    else:
        print('{} resulted in empty df'.format(wildcard))


if __name__ == "__main__":
    crall_all_counties()
    #crall_county('Santa Clara')
