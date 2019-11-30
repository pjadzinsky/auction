import glob
import json
import logging
import os
import re
import time
from html.parser import HTMLParser

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import numpy as np
import pandas as pd

from auction.config import ACTIVE_AUCTION_FOLDER, COUNTIES, CANCELED_FOLDER, PROJ_ROOT,\
    URL_FOLDER, AUCTIONED_FOLDER, UNKNOWN_FOLDER, COLUMNS

AUCTION_COM = "http://www.auction.com"

logger = logging.getLogger(__name__)


class AuctionIDParser(HTMLParser):
    """
    This parser is meant to be used with a search from auction.com returning a list of properties. The only thing
    it does is to look for values of the form:
    <a
        href="/details/445-oak-grove-ave-menlo-park-ca-94025-2832559-e_13443"
        class="root_link_2RdM role-primary_link_1hiH asset-root_styles_3IrY u-pt-3_styles_N-80 u-pb-3_styles_3gbq u-pl-3_styles_Nm3P u-pr-3_styles_2-gC"
        data-elm-id="asset_2832559_root"
        data-position="0"
        data-gtm-vis-first-on-screen-113070_481="873"
        data-gtm-vis-recent-on-screen-113070_481="12070"
        data-gtm-vis-total-visible-time-113070_481="100"
        data-gtm-vis-has-fired-113070_481="1">

    and extracts the link associated with href and the property id associated with data-elm-id="asset_<id>_root"

    By using this method, attr href is set, a dictionary mapping property_id (int) to href (str)
    """
    href = dict()
    root_regex = re.compile('asset_[0-9]*_root')

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for attr, value in attrs:
                if attr == 'href':
                    href = value
                if self.root_regex.match(value):
                    _, property_id_str, _ = value.split('_')
                    self.href[int(property_id_str)] = href
                    return

    def handle_endtag(self, tag):
        pass

    def handle_data(self, data):
        pass

    def set_column(self, attrs):
        pass


def get_chrome_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.binary_location = '/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary'

    driver = webdriver.Chrome(executable_path=os.path.abspath("chromedriver"), chrome_options=chrome_options)
    return driver


def get_auction_ids(driver, auction_id_parser, date_str, search_str, suffix=' County, CA'):
    """
    This method searches in auction.com with some 'search_str' criteria and parsers the html to extract
    the Auction ID and associated href and stores them in attribute 'href' of 'auction_id_parser' (a dictionary
    mapping auction_id to href)

    All the heavy work is done by the auction_id_parser

    :param driver: output of get_chrome_driver
    :param auction_id_parser: an instance of parse_url.AuctionIDParser
    :param county: str, 'Alameda' or similar
    :return:
    """
    driver.get(AUCTION_COM)
    search_str = search_str + suffix

    logger.info('working on {}'.format(search_str))
    search_field = driver.find_element_by_name("Search")

    search_field.clear()
    search_field.send_keys(search_str)
    search_field.send_keys(Keys.RETURN)
    time.sleep(5)

    # pagination starts at i = 1
    i = 1
    while True:
        auction_id_parser.feed(driver.page_source)
        filename = os.path.join(URL_FOLDER, '{}_{}_{}.html'.format(search_str, date_str, i))
        with open(filename, 'w+t') as fid:
            fid.write(driver.page_source)

        try:
            next_button = driver.find_element_by_link_text(str(i))
            next_button.click()
            i += 1
        except:
            break


def find_drivers_finder(driver, attr):
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
            logger.info(finder)
        except:
            continue


def crawl_all_counties(today_str, force=False):
    """
    Wrapper to call crawl_county on each County in config.COUNTIES
    Saves output to active <Date>.json
    It also logger.infos how many properties it found per county at the end
    :return:
    """

    # if we already have a json file, load it and return it
    json_file = os.path.join(PROJ_ROOT, ACTIVE_AUCTION_FOLDER, '{}.json'.format(today_str))
    if os.path.isfile(json_file) and not force:
        with open(json_file) as fid:
            temp_dir = json.load(fid)
            # we are saving keys as strings rather than ints, we convert them as soon as we load them back
            auction_id_href = {int(k): v for k, v in temp_dir.items()}
            logger.info('json file found, loaded with {} auctions'.format(len(auction_id_href)))
    else:
        driver = get_chrome_driver()
        auction_id_parser = AuctionIDParser()
        for county in COUNTIES:
            get_auction_ids(driver, auction_id_parser, today_str, county)

        driver.close()
        with open(json_file, 'w+t') as fid:
            json.dump(auction_id_parser.href, fid, indent=4)

        auction_id_href = auction_id_parser.href

    return auction_id_href


def crawl_state(today_str, state):
    driver = get_chrome_driver()
    auction_id_parser = AuctionIDParser()

    # if I already got a json file for today_str, add it to auction_id_parser
    json_file = os.path.join(PROJ_ROOT, ACTIVE_AUCTION_FOLDER, '{}.json'.format(today_str))
    if os.path.isfile(json_file):
        with open(json_file) as fid:
            href = json.load(json_file)
            auction_id_parser.href = href

    get_auction_ids(driver, auction_id_parser, today_str, state, suffix=' state')
    driver.close()
    with open(json_file, 'w+t') as fid:
        json.dump(auction_id_parser.href, fid, indent=4)

    auction_id_href = auction_id_parser.href

    return auction_id_href


def start_clean(save_str):
    # grab all auctions and href we ever recorded, 'hrefs' is a dictionary mapping auction_id to href
    hrefs = merge_all_json('active')
    driver = get_chrome_driver()
    df = pd.DataFrame([], columns=COLUMNS)

    for i, (auction_id, href) in enumerate(hrefs.items(), 1):
        try:
            msg = 'extracting info for active auction: {}, {}/{}'.format(auction_id, i, len(hrefs))
            auction_series = get_single_auction_data(auction_id, href, driver, force=False, msg=msg)
            df.loc[auction_id] = auction_series
        except Exception as e:
            logger.exception(e)

    all_status = ['active', 'auctioned', 'canceled', 'unknown']
    seen_status = np.unique(df.my_status).tolist()
    print(all_status)
    print(seen_status)
    try:
        assert all_status == seen_status
    except:
        all_status.remove('unknown')
        assert all_status == seen_status


    def save_df(df, which, folder, save_name):
        sub_df = df[df.my_status == which]
        sub_df.to_csv(os.path.join(folder, '{}.csv'.format(save_name)))

    # split df into 'active', 'auctioned', 'cancel', 'unknown'
    save_df(df, 'active', ACTIVE_AUCTION_FOLDER, save_str)
    save_df(df, 'auctioned', AUCTIONED_FOLDER, save_str)
    save_df(df, 'canceled', CANCELED_FOLDER, save_str)
    save_df(df, 'unknown', UNKNOWN_FOLDER, save_str)



def find_duplicates(df):
    df.sort_index(inplace=True)
    diff = np.diff(df.index.to_list())
    if min(diff) == 0:
        idxs = np.where(diff==0)[0]
        return df.index[idxs]


def load_all(folder):
    all_csvs = glob.glob(os.path.join(folder, '*.csv'))
    all_csvs.sort()
    df = pd.DataFrame([])
    for csv in all_csvs:
        df = df.append(pd.read_csv(csv))

    df = df.groupby('auction_id').last()
    df.index = df.index.astype(int)
    return df


def merge_all_json(folder):
    all_files = glob.glob(os.path.join(folder, '*.json'))
    all_files.sort()
    final_d = {}
    for f in all_files:
        with open(f) as fid:
            d = json.load(fid)
            final_d.update(d)
    return final_d


def download_href(auction_id, href, driver, force, msg):
    """
    download and save url associated with href

    :param auction_id: int
    :param href:  str, url to download
    :param driver:
    :param force: bool:
        True, forces downloading data from server
        False, if local_name exists will load content from file
    :return:
    """
    local_name = os.path.join(PROJ_ROOT, URL_FOLDER, '{}.html'.format(auction_id))
    if force or not os.path.isfile(local_name):
        logger.info(msg)
        url = AUCTION_COM + href
        driver.get(url)
        time.sleep(3)
        with open(local_name, 'w+t') as fid:
            fid.write(driver.page_source)


def get_single_auction_data(auction_id, href, driver, force, msg):
    """
    Get pd.Series for given auction_id. If we already have a local copy we'll use that copy without
    downloading data from server (unless 'force' is set)
    :param auction_id: int
    :param href:  str, url to download
    :param driver:
    :param force: bool:
        True, forces downloading data from server
        False, if local_name exists will load content from file
    :return:
    """
    local_name = os.path.join(PROJ_ROOT, URL_FOLDER, '{}.html'.format(auction_id))
    if os.path.isfile(local_name) and not force:
        with open(local_name) as fid:
            html_text = fid.read()
    else:
        logger.info(msg)
        url = AUCTION_COM + href
        driver.get(url)
        time.sleep(3)
        with open(local_name, 'w+t') as fid:
            fid.write(driver.page_source)
        html_text = driver.page_source

    auction_series = extract_property_series(html_text)
    auction_series['href'] = href
    auction_series.name = int(auction_id)
    return auction_series

##########################
# All pages open were returned by verify_csv('auctioned') and are wrong
# I have to test why they were wrongly classified




def add_my_status(s):
    # Completed - Reverted to Beneficiary   belongs to active
    # Completed - Sold to 3rd Party         belongs to auctioned
    # Completed - Pending Sale Result       belongs to auctioned
    # Pending                               ?
    # For Sale                              belongs to active
    # Active - Scheduled for Auction        belongs to active
    # Sold                                  belongs to auctioned
    # Gone                                  belongs to auctioned?
    if 'status_label' not in s:
        s['my_status'] = 'canceled'
    elif s['status_label'].startswith('Active') or s['status_label'].startswith('For Sale') or \
            s['status_label'].startswith('Completed - Reverted to Beneficiary'):
        s['my_status'] = 'active'
    elif s['status_label'] == 'Pending' or \
        s['status_label'] == 'Sold' or \
        s['status_label'].startswith('Completed - Sold to 3rd Party') or \
        s['status_label'].startswith('Completed - Pending Sale Result'):
            s['my_status'] = 'auctioned'
    else:
        s['my_status'] = 'unknown'
        logger.info('Did not classify {} correctly'.format(s['my_status']))


def fix_address(df, filename):
    """
    Some html have property_address, some have street_name (or city instead of property_city or postal_code instead
    of property_zip) This resulted in some rows with NaN because I was not extracting fields street_name,
    postal_code, city

    :param df:
    :return:
    """
    driver = get_chrome_driver()
    for auction_id, row in df.iterrows():
        if isinstance(row.property_address, float) or isinstance(row.property_city, float):
            msg = "Fixing information for {}".format(auction_id)
            force = False
            href = row.href
            new_row = get_single_auction_data(auction_id, href, driver, force, msg)
            df.loc[auction_id] = new_row
    df.to_csv(filename)


