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
import logging
import os
import traceback
import webbrowser

import pandas as pd

from going_headless import auction_crawler
import zillow

from config import COMPLETED_FOLDER, ACTIVE_AUCTION_FOLDER, CANCELED_FOLDER, LOGS, AUCTIONED_FOLDER, PROJ_ROOT

logger = logging.getLogger(__name__)
HALF_YEAR = timedelta(days=182)


def remove_properties(from_here, that_are_in_here):
    ids_to_remove = that_are_in_here.index
    all_ids = from_here.index
    missing_ids = set(all_ids).difference(ids_to_remove)
    missing_df = from_here.loc[missing_ids]
    return missing_df


def zillowfy(today_str):
    """
    Load last csv from AUCTIONED_FOLDER (these are all the properties that according to auction.com
    were auctioned)
    For each property get data from zillow.
    If last sold date > auctioned_date, update information accordingly
    Properties with data from zillow are pulled out of the AUCTIONED_FOLDER and saved onto the
    COMPLETED_FOLDER
    """
    auctioned, auctioned_filename = auction_crawler.load_last_df(AUCTIONED_FOLDER)
    for index, data in auctioned.iterrows():
        address = data['property_address']
        zipcode = data['property_zip']
        try:
            summary = zillow.get_summary(address, zipcode)
        except Exception as e:
            logger.exception(e)
            logger.info('{}, {}'.format(address, zipcode))
        if not hasattr(summary, 'zillow_id'):
            logger.info('No zillow data for {}, {}'.format(address, zipcode))

        if summary.last_sold_date:
            last_sold_date = datetime.strptime(summary.last_sold_date, '%m/%d/%Y').date()
            auction_date = datetime.strptime(data['auction_date'], '%Y-%m-%d').date()
            if auction_date <= last_sold_date:
                auctioned.loc[index, 'zillow_id'] = summary.zillow_id
                auctioned.loc[index, 'zestimate_amount'] = summary.zestimate_amount
                auctioned.loc[index, 'zestimate_valuation_range_high'] = summary.zestimate_valuation_range_high
                auctioned.loc[index, 'zestimate_valuation_range_low'] = summary.zestimate_valuationRange_low
                auctioned.loc[index, 'zillow_last_date_sold'] = last_sold_date
                auctioned.loc[index, 'zillow_lasl_sold_price'] = summary.last_sold_price
                logger.info('{}, {} sold on {} for {}{}'.format(address,
                                                                zipcode,
                                                                last_sold_date,
                                                                summary.last_sold_price,
                                                                summary.last_sold_price_currency))

    if 'zillow_id' in auctioned:
        index_completed = auctioned['zillow_id'].dropna().index
        if not index_completed.empty:
            completed = auctioned.loc[index_completed]
            auctioned.drop(index_completed, inplace=True)

            basename = "{}.csv".format(today_str)
            completed.to_csv(os.path.join(PROJ_ROOT, COMPLETED_FOLDER, basename))
            auctioned.to_csv(auctioned_filename)


def parse_date(date_str):
    today = date.today()
    auction_year = today.year
    if '-' in date_str:
        # date_str is of the form 'Sep 2 - 4'
        month_str, _, _, auction_day = date_str.split()
    elif 'TBD' in date_str:
        # date_str is of the form 'Sep 04, Time TBD'
        month_str, auction_day, _, _ = date_str.split()
        auction_day = auction_day[:-1]  # remove ',' after number
    else:
        # date_str is of the form 'Sep 04, 9:00am'
        month_str, auction_day, _ = date_str.split()
        auction_day = auction_day[:-1]

    auction_day = int(auction_day)
    # hack, don't know of a better way to convert month_str to month number
    auction_month = datetime.strptime('2000 {} 01'.format(month_str), '%Y %b %d').month

    # it could be that auction date is in the past (last month or so) but it could also be
    # that we are in November and auction is in January or February. In that case auction_date
    # just computed will be wrong since we are using the today's year. Not sure if this will
    # always work
    if auction_month < 6 and today.month > 6:
        auction_year += 1

    auction_date = date(auction_year, auction_month, auction_day)

    return auction_date


def verify_csv(folder, url_head='http://www.auction.com'):
    """
    Create links to easily verify that properties in this folder are correctly categorized:
    """
    with open('links.txt', 'w+t') as fid:
        df, _ = auction_crawler.load_last_df(folder)
        for index, row in df.iterrows():
            url = url_head + row.href
            fid.write(url + '\n')
            webbrowser.open(url, new=2)


if __name__ == "__main__":
    logging.basicConfig(filename=LOGS,
                        format='%(levelname).1s:%(module)s:%(lineno)d:%(asctime)s: %(message)s',
                        level=logging.INFO)
    logger.info('*' * 80)
    today_str = date.today().strftime('%Y%m%d')

    recompute = True

    if recompute:
        hrefs = auction_crawler.crawl_all_counties(today_str)
        auction_crawler.crawl_individual_auction_ids(today_str, hrefs)
    zillowfy(today_str)

# Completed - Reverted to Beneficiary
# Completed - Sold to 3rd Party
# Completed - Pending Sale Result
# For Sale
# Active - Scheduled for Auction
#https://www.auction.com/details/550-mcfall-ct-santa-rosa-ca-95401-2663728-e_13547 for Sale
#https://www.auction.com/details/123-nolan-ct-forestville-ca-95436-2833233-e_13547a scheduled
# /details/1574-willowmont-ave-san-jose-ca-95118-2791151-e_13391a still active, why in canceled?
#https://www.auction.com/details/2433-rockingham-cir-lodi-ca-95242-2745060-e_13547a scheduled
#https://www.auction.com/details/7625-zilli-drive-tracy-ca-95304-2842860-e_900x scheduled for auction
#https://www.auction.com/details/1545-yardley-st-santa-rosa-ca-95403-2799767-e_13443a scheduled for auction
#https://www.auction.com/details/1221-enview-ct-stockton-ca-95210-2838647-e_13443 sold to 3rd party
#https://www.auction.com/details/1121-el-vecino-avenue-modesto-ca-95350-2233215-e_13443 completed, sold to 3rd party
#https://www.auction.com/details/5021-tacomic-drive-sacramento-ca-95842-2840729-e_900x still active
#https://www.auction.com/residential/1815%20KAGEHIRO%20DR%2C%20TRACY%2C%20CA_qs/pending,closed,canceled_lt/ Correctly canceled
## the one before was not understood
#https://www.auction.com/details/340-fieldbrook-ln-watsonville-ca-95076-2805840-e_13391a idem
#https://www.auction.com/details/2410-madden-ter-san-jose-ca-95116-2805990-e_13391a idem
