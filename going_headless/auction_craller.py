import glob
import json
import os
import time
from datetime import date

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

import pandas as pd

import parse_url
from config import COUNTIES, URL_FOLDER, PROJ_ROOT, ACTIVE_AUCTION_FOLDER
AUCTION_COM = "http://www.auction.com"


def get_chrome_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.binary_location = '/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary'

    driver = webdriver.Chrome(executable_path=os.path.abspath("chromedriver"), chrome_options=chrome_options)
    return driver


def get_auction_ids(driver, auction_id_parser, search_str, suffix=' County, CA'):
    """
    This method searches properties in auction.com in the given county and parsers the html to extract
    the Auction ID (added in place to attribute auction_ids of auction_id_parser)

    :param driver: output of get_chrome_driver
    :param auction_id_parser: an instance of parse_url.AuctionIDParser
    :param county: str, 'Alameda' or similar
    :return:
    """
    driver.get(AUCTION_COM)
    search_str = search_str + suffix

    print('working on {}'.format(search_str))
    search_field = driver.find_element_by_name("Search")

    search_field.clear()
    search_field.send_keys(search_str)
    search_field.send_keys(Keys.RETURN)
    time.sleep(5)
    driver.save_screenshot('/tmp/{}.png'.format(search_str))

    # pagination starts at i = 1
    i = 1
    while True:
        auction_id_parser.feed(driver.page_source)
        try:
            next_button = driver.find_element_by_link_text(str(i))
            next_button.click()
            i += 1
        except:
            break


def get_auction_id_metadata(driver, metadata_parser, url):
    """
    For the given auction_id, grab all the metadata and create a pd.Series with it.

    :param driver:
    :param metadata_parser:
    :param auction_id:
    :return: pd.Series with metadata
    """
    driver.get(url)
    time.sleep(5)
    metadata_parser.feed(driver.page_source)


"""
def crall_county(county, today_str):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.binary_location = '/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary'

    driver = webdriver.Chrome(executable_path=os.path.abspath("chromedriver"), chrome_options=chrome_options)
    driver.get(AUCTION_COM)

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
"""


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


def crall_all_counties(today_str):
    """
    Wrapper to call crall_county on each County in config.COUNTIES
    Saves output to active_auction <Date>.json
    It also prints how many properties it found per county at the end
    :return:
    """

    # if we already have a json file, load it and return it
    json_file = os.path.join(PROJ_ROOT, ACTIVE_AUCTION_FOLDER, '{}.json'.format(today_str))
    if os.path.isfile(json_file):
        with open(json_file) as fid:
            temp_dir = json.load(fid)
            # we are saving keys as strings rather than ints, we convert them as soon as we load them back
            auction_id_href = {int(k): v for k, v in temp_dir.items()}
            print('json file found, loaded with {} auctions'.format(len(auction_id_href)))
    else:
        driver = get_chrome_driver()
        auction_id_parser = parse_url.AuctionIDParser()
        for county in COUNTIES:
            get_auction_ids(driver, auction_id_parser, county)

        driver.close()
        with open(json_file, 'w+t') as fid:
            json.dump(auction_id_parser.href, fid, indent=4)

        auction_id_href = auction_id_parser.href

    return auction_id_href


def crall_all_addresses(today_str, addresses):
    """
    Wrapper to call crall_county on each County in config.COUNTIES
    It also prints how many properties it found per county at the end
    :return:
    """

    # if we already have a json file, load it and return it
    driver = get_chrome_driver()
    auction_id_parser = parse_url.AuctionIDParser()
    for address in addresses:
        get_auction_ids(driver, auction_id_parser, address)
        print(len(auction_id_parser.href))

    driver.close()

    json_file = os.path.join(PROJ_ROOT, ACTIVE_AUCTION_FOLDER, 'from_addresses_{}.json'.format(today_str))
    with open(json_file, 'w+t') as fid:
        json.dump(auction_id_parser.href, fid, indent=4)

    auction_id_href = auction_id_parser.href

    return auction_id_href


def crall_individual_auction_ids(today_str, auction_id_href):
    driver = get_chrome_driver()
    # now we load the last active_auction dataframe we have in file. This is outdated info
    # but the last one we got
    active_auction_df = load_last_df(os.path.join(PROJ_ROOT, 'active_auction'))

    # We have to identify auction ids for which we don't have info yet
    active_ids = set(auction_id_href.keys())
    new_auction_ids = active_ids.difference(active_auction_df.index)
    print('action_crawler identified {} new properties'.format(len(new_auction_ids)))

    # We have to identify auction ids that were active before but are no longer active
    deactivated_ids = set(active_auction_df.index).difference(active_ids)
    print('action_crawler identified {} deactivated properties'.format(len(deactivated_ids)))

    # legacy data transfomration
    deactivated_df = active_auction_df.loc[deactivated_ids]
    addresses = deactivated_df[['asset_address_content_1', 'asset_address_content_2']].apply(
        lambda x: x.asset_address_content_1 + ', ' + x.asset_address_content_2, axis=1)

    auction_id_parser = parse_url.AuctionIDParser()
    for address in addresses:
        CA_index = address.rfind('CA ')
        address = address[:CA_index + 2]
        get_auction_ids(driver, auction_id_parser, address, suffix='')
        print(len(auction_id_parser.href))

    with open(today_str + 'addresses.json', 'w+t') as fid:
        json.dump(auction_id_parser.href, fid, indent=4)
    # add missing auction_ids to previously_active
    """
    for auction_id in new_auction_ids:
        try:
            href = auction_id_href[auction_id]
            auction_series = get_single_auction_data(auction_id, href, driver)
            active_auction_df = active_auction_df.append(auction_series)
        except:
            print('problem with id: {}'.format(auction_id))
    """

    deactivated_df = pd.DataFrame()
    for auction_id in deactivated_ids:
        href = auction_id_href[auction_id]    # we are done crawling
        auction_series = get_single_auction_data(auction_id, href, driver)
        deactivated_df = deactivated_df.append(auction_series)
        print(auction_series)
    driver.close()

    active_auction_df.to_csv(os.path.join(PROJ_ROOT, ACTIVE_AUCTION_FOLDER, '{}.csv'.format(today_str)))
    return active_auction_df


def load_last_df(folder):
    all_csvs = glob.glob(os.path.join(folder, '*.csv'))
    if all_csvs:
        last_csv = sorted(all_csvs)[-1]
        df = pd.read_csv(last_csv, index_col=0)
        print('just loaded df from', last_csv)
    else:
        df = pd.DataFrame([])
        df.index.name = 'auction_id'

    return df


def get_single_auction_data(auction_id, href, driver):
    print('extracting info for active auction: {}'.format(auction_id))
    url = AUCTION_COM + href
    driver.get(url)
    time.sleep(3)
    auction_series = parse_url.extract_property_series(driver.page_source)
    auction_series['href'] = href
    auction_series.name = int(auction_id)
    return auction_series


if __name__ == "__main__":
    today_str = date.today().strftime('%Y%m%d')
    hrefs = crall_all_counties(today_str)
    crall_individual_auction_ids(today_str, hrefs)


