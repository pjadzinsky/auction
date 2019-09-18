import glob
import json
import logging
import os
import re
import time
from datetime import date
from html.parser import HTMLParser

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import numpy as np
import pandas as pd

from config import ACTIVE_AUCTION_FOLDER, COMPLETED_FOLDER, COUNTIES, KEYS_TO_EXTRACT, \
    PENDING_TRANSACTION_FOLDER, PROJ_ROOT, URL_FOLDER, READY_FOR_ZILLOW_FOLDER
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


def get_auction_ids(driver, auction_id_parser, search_str, suffix=' County, CA'):
    """
    This method searches in auction.com with some 'search_str' criteria and parsers the html to extract
    the Auction ID and associated href and stores them in attribute 'href' of 'auction_id_parser'

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


def crawl_all_counties(today_str):
    """
    Wrapper to call crawl_county on each County in config.COUNTIES
    Saves output to active_auction <Date>.json
    It also logger.infos how many properties it found per county at the end
    :return:
    """

    # if we already have a json file, load it and return it
    json_file = os.path.join(PROJ_ROOT, ACTIVE_AUCTION_FOLDER, '{}.json'.format(today_str))
    if os.path.isfile(json_file):
        with open(json_file) as fid:
            temp_dir = json.load(fid)
            # we are saving keys as strings rather than ints, we convert them as soon as we load them back
            auction_id_href = {int(k): v for k, v in temp_dir.items()}
            logger.info('json file found, loaded with {} auctions'.format(len(auction_id_href)))
    else:
        driver = get_chrome_driver()
        auction_id_parser = AuctionIDParser()
        for county in COUNTIES:
            get_auction_ids(driver, auction_id_parser, county)

        driver.close()
        with open(json_file, 'w+t') as fid:
            json.dump(auction_id_parser.href, fid, indent=4)

        auction_id_href = auction_id_parser.href

    return auction_id_href


def crawl_individual_auction_ids(today_str, auction_id_href):
    driver = get_chrome_driver()
    # now we load the last active_auction dataframe we have in file. This is outdated info
    # but the last one we got
    active_auction_df = load_last_df(os.path.join(PROJ_ROOT, 'active_auction'))

    # We have to identify auction ids for which we don't have info yet
    active_ids = set(auction_id_href.keys())
    new_auction_ids = active_ids.difference(active_auction_df.index)
    logger.info('action_crawler identified {} new properties'.format(len(new_auction_ids)))

    # We have to identify auction ids that were active before but are no longer active
    deactivated_ids = set(active_auction_df.index).difference(active_ids)
    logger.info('action_crawler identified {} deactivated properties'.format(len(deactivated_ids)))

    deactivated_df = load_last_df(os.path.join(PROJ_ROOT, PENDING_TRANSACTION_FOLDER))
    deactivated_df = deactivated_df.append(active_auction_df.loc[deactivated_ids])
    deactivated_df.drop_duplicates(inplace=True)
    active_auction_df.drop(deactivated_ids, inplace=True)

    # legacy data transfomration
    """
    deactivated_df = active_auction_df.loc[deactivated_ids]
    addresses = deactivated_df[['asset_address_content_1', 'asset_address_content_2']].apply(
        lambda x: x.asset_address_content_1 + ', ' + x.asset_address_content_2, axis=1)

    auction_id_parser = AuctionIDParser()
    for address in addresses:
        CA_index = address.rfind('CA ')
        address = address[:CA_index + 2]
        get_auction_ids(driver, auction_id_parser, address, suffix='')
        logger.info(len(auction_id_parser.href))

    with open(today_str + 'addresses.json', 'w+t') as fid:
        json.dump(auction_id_parser.href, fid, indent=4)
    """
    # add missing auction_ids to previously_active
    for auction_id in new_auction_ids:
        try:
            href = auction_id_href[auction_id]
            auction_series = get_single_auction_data(auction_id, href, driver, force=False)
            active_auction_df = active_auction_df.append(auction_series)
        except Exception as e:
            logger.error('problem with id: {}'.format(auction_id))

    for auction_id, href in deactivated_df.href.iteritems():
        if not href:
            logger.info('{} key has no href'.format(auction_id))
            continue

        try:
            auction_series = get_single_auction_data(auction_id, href, driver, force=True)
            deactivated_df.loc[auction_id] = auction_series
        except Exception as e:
            logger.exception(e)
    driver.close()

    basename = '{}.csv'.format(today_str)
    to_zillowfy_df = deactivated_df[deactivated_df.status_label == 'Completed - Pending Sale Result']
    deactivated_df.drop(to_zillowfy_df.index, inplace=True)

    active_auction_df.to_csv(os.path.join(PROJ_ROOT, ACTIVE_AUCTION_FOLDER, basename))
    deactivated_df.to_csv(os.path.join(PROJ_ROOT, PENDING_TRANSACTION_FOLDER, basename))
    to_zillowfy_df.to_csv(os.path.join(PROJ_ROOT, READY_FOR_ZILLOW_FOLDER, basename))
    return active_auction_df


def find_duplicates(df):
    df.sort_index(inplace=True)
    diff = np.diff(df.index.to_list())
    if min(diff) == 0:
        idxs = np.where(diff==0)[0]
        return df.index[idxs]

def load_last_df(folder):
    all_csvs = glob.glob(os.path.join(folder, '*.csv'))
    if all_csvs:
        last_csv = sorted(all_csvs)[-1]
        df = pd.read_csv(last_csv, index_col=0)
        logger.info('just loaded df from {}'.format(last_csv))
    else:
        df = pd.DataFrame([])
        df.index.name = 'auction_id'

    return df


def get_single_auction_data(auction_id, href, driver, force):
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
            html_text = fid.readlines()
    else:
        logger.info('extracting info for active auction: {}'.format(auction_id))
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


def extract_property_series(html_txt):
    """ From the html code that we get when clicking a particular property on auction.com (after a search)
    exctract the pd.Series with all the data that we are going to keep
    return pd.Series, name of the series will be the auction_id but that is not done here. Also
    the series lacks the href
    """
    html_lines = html_txt.split('\n')
    with open('/tmp/html.txt', 'w+t') as fid:
        fid.write(html_txt)

    for line in html_lines:
        line = line.strip()
        if line.startswith('window.INITIAL_STATE'):
            line = line.replace('window.INITIAL_STATE = ', '')
            line = line[:-1]
            d = json.loads(line)

            s = pd.Series()
            def extract_field(d, s, keys):
                for k, v in d.items():
                    if isinstance(v, dict):
                        extract_field(v, s, keys)
                    elif k in keys:
                        if k == 'images':
                            v = len(v)
                        s[k] = v

            # below doesn't seem to work anymore as of 2019, Sep 14.
            # Initial dictory has keys:
            # 'verificationModalReducer', 'user', 'properties', 'modals', 'contracting', 'form', 'queues', 'bidding', 'message', 'featureFlags', 'biddingDeposit', 'propertyAnalytics', 'purchaseProfiles', 'finalOffer'])
            # Most of them are useless except:
            # properties    property info
            # contracting ? (is empty but might be good when in contract)

            extract_field(d, s, KEYS_TO_EXTRACT)
            break
    return s


