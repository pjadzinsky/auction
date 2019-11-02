"""
1. I generated html files in 'urls' by following 'gioloe' response here
https://stackoverflow.com/questions/3314429/how-to-view-generated-html-code-in-firefox/3314453#3314453
    I found the element in the html that when I hover over, highlights the whole table of properties.
    Then copy pasted the html into 'urls' folder
2. Pass those files to parse_url.process_html_files(files)
    This step generates active/<date>.active with all data from auction.com
3. How do we know if auction finished succesfully? Call zillow to get estimated value/rents and
    once transaction closes the executed price

"""
from datetime import date, datetime, timedelta
import glob
import json
import logging
import os
import traceback
import webbrowser

import pandas as pd

from going_headless import auction_crawler
import zillow

from config import COMPLETED_FOLDER, ACTIVE_AUCTION_FOLDER, CANCELED_FOLDER, LOGS, AUCTIONED_FOLDER, PROJ_ROOT, \
    COLUMNS, ZILLOWED_FOLDER, URL_FOLDER, KEYS_TO_EXTRACT, REPLACE_LIST

logger = logging.getLogger(__name__)
HALF_YEAR = timedelta(days=182)


def remove_properties(from_here, that_are_in_here):
    ids_to_remove = that_are_in_here.index
    all_ids = from_here.index
    missing_ids = set(all_ids).difference(ids_to_remove)
    missing_df = from_here.loc[missing_ids]
    return missing_df


def zillowfy_list(auction_ids, days=90):
    folder = os.path.join(PROJ_ROOT, ZILLOWED_FOLDER)
    csv_files = select_files(days, 0, ZILLOWED_FOLDER, 'csv')
    df = merge_df(csv_files, index_col=0)

    all_series = []
    for auction_id, href in auction_ids.items():
        if auction_id in df.index:
            continue

        summary = zillowfy(auction_id, href)
        if hasattr(summary, 'last_sold_date') and summary.last_sold_date:
            last_sold_date = summary.last_sold_date
            m_s, d_s, y_s = last_sold_date.split('/')
            sold_date = date(int(y_s), int(m_s), int(d_s))
            today = date.today()
            if sold_date > today - timedelta(days=days):
                s1 = extract_zillow_series(summary)
                s2 = extract_auction_series(auction_id)
                s = s1.append(s2)
                s.name = auction_id
                all_series.append(s)

    if all_series:
        for s in all_series:
            if df.empty:
                df = s.to_frame().T
            else:
                df.loc[s.name] = s

        df.to_csv(os.path.join(folder, '{}.csv'.format(date_str(0))))


def extract_zillow_series(summary):
    s = pd.Series()
    s['zillow_id'] = summary.zillow_id
    s['zestimate_amount'] = summary.zestimate_amount
    s['zestimate_valuation_range_high'] = summary.zestimate_valuation_range_high
    s['zestimate_valuation_range_low'] = summary.zestimate_valuationRange_low
    s['zillow_last_date_sold'] = summary.last_sold_date
    s['zillow_last_sold_price'] = summary.last_sold_price
    return s


def extract_auction_series(auction_id, href=None):
    """ From the html code that we get when clicking a particular property on auction.com (after a search)
    exctract the pd.Series with all the data that we are going to keep
    return pd.Series, name of the series will be the auction_id but that is not done here. Also
    the series lacks the href
    """
    line = extract_window_line_from_html(auction_id)
    if not line and href:
        # try downloading again html from href
        print('missing line for {}, downloading href again'.format(auction_id))
        driver = auction_crawler.get_chrome_driver()
        force = True
        msg = ''
        auction_crawler.download_href(auction_id, href, driver, force, msg)
        line = extract_window_line_from_html(auction_id)
        if line:
            print('Problem fixed, new html has "line"')
    if not line:
        print('missing line for {}'.format(auction_id))
        return pd.Series()

    d = json.loads(line)

    s = pd.Series()
    def extract_field(d, s, keys):
        for k, v in d.items():
            if k == 'similarProperties':
                # don't get any info from these
                continue
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

    rename_index(s)
    if os.environ.get('DEBUGGING_AUCTION') and not ('property_address' in s and 'property_zip' in s):

        with open('/tmp/{}.json'.format(auction_id), 'w+t') as fid:
            if "propertyAnalytics" in d and "similarProperties" in d["propertyAnalytics"]:
                del d["propertyAnalytics"]["similarProperties"]
            if 'seoLinks' in d:
                del d['seoLinks']
            json.dump(d, fid, indent=4)
    return s


def zillowfy(auction_id, href):
    summary = None
    address, zipcode = get_address_and_zipcode(auction_id, href)

    if address and zipcode:
        try:
            summary = zillow.get_summary(address, zipcode)
        except Exception as e:
            logger.exception(e)
            logger.info('auction_id: {}, {}, {}'.format(auction_id, address, zipcode))
    return summary


def get_address_and_zipcode(auction_id, href):
    """
    Get pd.Series for given auction_id. We use a local copy of url
    :param auction_id: int or str
    :return: address and zipcode
    """
    # For the time being, extract_auction_series is called twice. In the future I might
    # have a simpler method that returns just the property_address and the zip and another one that pulls
    # all other info
    auction_series = extract_auction_series(auction_id, href)
    try:
        address = auction_series['property_address']
        zip = int(auction_series['property_zip'])
    except Exception as e:
        logger.info('Problem getting address/zip from {}'.format(auction_id))
        print('#'*80)
        print(auction_series)
        #logger.exception(e)
        address, zip = None, None

    return address, zip

    ##########################
    # All pages open were returned by verify_csv('auctioned') and are wrong
    # I have to test why they were wrongly classified


def extract_window_line_from_html(auction_id):
    html_lines = []
    local_name = os.path.join(PROJ_ROOT, URL_FOLDER, '{}.html'.format(auction_id))
    if os.path.isfile(local_name):
        with open(local_name) as fid:
            html_lines = fid.readlines()
    result = ''

    for line in html_lines:
        line = line.strip()
        if line.startswith('window.INITIAL_STATE'):
            line = line.replace('window.INITIAL_STATE = ', '')
            result = line[:-1]
            break
    return result


def rename_index(s):
    for old, new in REPLACE_LIST.items():
        if new not in s and old in s:
            s[new] = s[old]
            del s[old]

def parse_date(date_str):
    today = date.today()
    auction_year = today.year
    if '-' in date_str:
        # date_str is of the form 'sep 2 - 4'
        month_str, _, _, auction_day = date_str.split()
    elif 'tbd' in date_str:
        # date_str is of the form 'sep 04, time tbd'
        month_str, auction_day, _, _ = date_str.split()
        auction_day = auction_day[:-1]  # remove ',' after number
    else:
        # date_str is of the form 'sep 04, 9:00am'
        month_str, auction_day, _ = date_str.split()
        auction_day = auction_day[:-1]

    auction_day = int(auction_day)
    # hack, don't know of a better way to convert month_str to month number
    auction_month = datetime.strptime('2000 {} 01'.format(month_str), '%y %b %d').month

    # it could be that auction date is in the past (last month or so) but it could also be
    # that we are in november and auction is in january or february. in that case auction_date
    # just computed will be wrong since we are using the today's year. not sure if this will
    # always work
    if auction_month < 6 and today.month > 6:
        auction_year += 1

    auction_date = date(auction_year, auction_month, auction_day)

    return auction_date


def verify_csv(folder, url_head='http://www.auction.com', max_=10):
    """
    create links to easily verify that properties in this folder are correctly categorized:
    """
    with open('links.txt', 'w+t') as fid:
        df, _ = load_last_df(folder)
        for i, (index, row) in enumerate(df.iterrows()):
            if i == max_:
                break
            url = url_head + row.href
            fid.write(url + '\n')
            webbrowser.open(url, new=2)


def download_all_new_hrefs():
    folder = os.path.join(PROJ_ROOT, ACTIVE_AUCTION_FOLDER)
    all_json = glob.glob(os.path.join(folder, '*'))
    all_json.sort()

    previous = all_json[-2]
    last = all_json[-1]

    with open(previous) as fid:
        previous_d = json.load(fid)
    with open(last) as fid:
        last_d = json.load(fid)

    driver = auction_crawler.get_chrome_driver()
    force = False
    for auction_id, href in last_d.items():
        if auction_id not in previous_d:
            msg = 'donwloading href for {}'.format(auction_id)
            auction_crawler.download_href(auction_id, href, driver, force, msg)


def date_str(n):
    """
    return the date as string corresponding to n days ago
    :param n:
    :return:
    """
    passed_date = date.today() - timedelta(days=n)
    passed_str = passed_date.strftime('%Y%m%d')
    return passed_str


def select_files(start, end, folder, format):
    """
    get all the 'format' files that are in between start and end (not including end)

    :param start: str of the form %y%m%d or int, if int will be converted to str
    :param end: idem start
    :param folder: str, 'active'
    :param format: str, 'json'
    :return:
    """
    if isinstance(start, int):
        start = date_str(start)
    if isinstance(end, int):
        end = date_str(end)
    all_files = glob.glob(os.path.join(folder, '*.{}'.format(format)))
    def filter_file(file_):
        date_str = file_.rsplit('/', 1)[1].replace('.' + format, '')
        result = start <= date_str and date_str < end
        return result

    all_files = list(filter(filter_file, all_files))
    all_files.sort()
    return all_files


def merge_json_files(files):
    files.sort()
    final_d = {}
    for f in files:
        with open(f) as fid:
            d = json.load(fid)
            final_d.update(d)

    final_d = {int(k):v for k, v in final_d.items()}
    return final_d


def deactivated_auction_ids(currently_active, days):
    previously_active_href = previously_active_properties(days)
    deactivated = {id_: href for id_, href in previously_active_href.items() if id_ not in currently_active}
    return deactivated


def previously_active_properties(days):
    """
    load all the json files (except the last one) generated in the last 'num_days'.
    these have all the properties that were active at some point in the past
    then load the last json.
    return a dict mapping auction_id to href for all properties that were active at some point but are not active
    any more

    :param days:
    :return:
    """
    start_date = date_str(days)
    end_date = date_str(0)
    folder = os.path.join(PROJ_ROOT, ACTIVE_AUCTION_FOLDER)
    format = 'json'
    json_files = select_files(start_date, end_date, folder, format)
    d = merge_json_files(json_files)
    return d


def merge_df(df_files, **read_csv_kwargs):
    """ Merge dfs from oldes to earliest. Every time we encounter a repeated row we update
    """
    if not df_files:
        final = pd.DataFrame()
    else:
        df_files.sort()
        dfs = [pd.read_csv(f, **read_csv_kwargs) for f in df_files]
        df = pd.concat(dfs, axis=0)
        df = df.groupby(level=0).last()
    return df


def load_last_df(folder, avoid_date=None):
    last_csv = None
    all_csvs = glob.glob(os.path.join(folder, '*.csv'))
    all_csvs.sort()

    if avoid_date:
        all_csvs = [csv for csv in all_csvs if avoid_date not in csv]
    if all_csvs:
        last_csv = sorted(all_csvs)[-1]
        df = pd.read_csv(last_csv, index_col=0)
        logger.info('just loaded df from {}'.format(last_csv))
    else:
        df = pd.DataFrame([], columns=COLUMNS)

        df.index.name = 'auction_id'

    df.index = df.index.astype(int)
    #if 'property_zip' in df:
    #    df.astype({'property_zip': int})
    return df, last_csv


def list_to_zillowfy(deactivated_hrefs, today_str):
    """
    Load last csv from ZILLOW_FOLDER (these are all the properties that we have already identified as sold)
    For any property in deactivated_hrefs that is not in the df, we will try to query zillow.
    For the time being I'm just creating a dict with the auction_ids to send to zillow api
    """
    zillowed_df, _ = load_last_df(ZILLOWED_FOLDER, today_str)

    needs_to_zillow = {}
    for auction_id, href in deactivated_hrefs.items():
        if auction_id not in zillowed_df.index:
            needs_to_zillow[auction_id] = href

    return needs_to_zillow


if __name__ == "__main__":
    days = 90
    os.environ['DEBUGGING_AUCTION'] = 'True'    # a string evaluating to True or False
    logging.basicConfig(filename=LOGS,
                        format='%(levelname).1s:%(module)s:%(lineno)d:%(asctime)s: %(message)s',
                        level=logging.INFO)
    logger.info('*' * 80)
    today_str = date.today().strftime('%Y%m%d')

    hrefs = auction_crawler.crawl_all_counties(today_str)
    download_all_new_hrefs()
    deactivated_hrefs = deactivated_auction_ids(hrefs, days=days)
    auction_ids = list_to_zillowfy(deactivated_hrefs, today_str)

    zillowfy_list(auction_ids, days)


