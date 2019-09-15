"""
1. I generated html files in 'urls' by following 'gioloe' response here
https://stackoverflow.com/questions/3314429/how-to-view-generated-html-code-in-firefox/3314453#3314453
    I found the element in the html that when I hover over, highlights the whole table of properties.
    Then copy pasted the html into 'urls' folder
2. Pass those files to parse_url.process_html_files(files)
    This step generates active_auction/<date>.active_auction with all data from auction.com
3. How do we know if auction finished succesfully? Call zillow to get estimated value/rents and
    once transaction closes the executed price

"""
from datetime import date, datetime, timedelta
import os

import pandas as pd

from going_headless import auction_craller
import zillow

import parse_url
from config import COMPLETED_FOLDER, ACTIVE_AUCTION_FOLDER, PENDING_TRANSACTION_FOLDER

HALF_YEAR = timedelta(days=182)


def main(wildcard):
    """
    We have 3 types of properties, each will live in a corresponding csv
    1. Properties that are actively in auction (active_df/ACTIVE_AUCTION_FOLDER)
    2. Properties that were identified in the past as being in auction, but for which we have no
        transaction data yet (pending_transaction_df/PENDING_TRANSACTION_FOLDER)
    3. Properties that were in auction in the past and for which we have gathered all the transaction
        data from zillow (completed_df/COMPLETED_FOLDER)


    :param wildcard: will process all html files in URL_FOLDER matching it
    :return:
    """
    # go to auction.com and get all properties being auctioned in all counties in config.COUNTIES
    # then for each property for which we don't yet have all the info, go into the property auction
    # page and extract such info. At the end, a new csv file will be created in ACTIVE_AUCTION_FOLDER
    # with all the properties currently active
    active_auctions_df = auction_craller.crall_all_counties()
    print(active_auctions_df.groupby('county').city.count())

    # the list of properties we have to zillowfy is compossed of:
    # 1. those that are already in this list
    # 2. those that are marked as pending in active_auctions_df
    # plus those properties in active_auctions_df, with
    pending_transaction_df = auction_craller.load_last_df(PENDING_TRANSACTION_FOLDER)

    # Get active auctions in 'files' to 'active_auctions_df'
    base_name = '{}.csv'.format(date.today().strftime('%Y%m%d'))

    # we only need to zillowfy properties that are not schedule (or active) in auction.com
    pending_transaction_df = remove_properties(pending_transaction_df, active_auctions_df)

    # change compute 'auction_end_date' from 'asset_auction_date'
    pending_transaction_df.loc[:, 'auction_end_date'] = pending_transaction_df['asset_auction_date'].apply(parse_date)

    # add data from zillow, properties in completed_df are removed from pending_transaction_df
    completed_df = zillowfy(pending_transaction_df)

    # next time we run, we only rely on pending_transaction properties. Any properties in this csv
    # that are not active, will be considered for zillowfy. We therefor have to save all properties
    # that are in pending_transaction_df + active_auctions_df
    pending_transaction_df = pending_transaction_df.append(active_auctions_df)
    active_auctions_df.to_csv(os.path.join(ACTIVE_AUCTION_FOLDER, base_name))
    completed_df.to_csv(os.path.join(COMPLETED_FOLDER, base_name))
    pending_transaction_df.to_csv(os.path.join(PENDING_TRANSACTION_FOLDER, base_name))


def remove_properties(from_here, that_are_in_here):
    ids_to_remove = that_are_in_here.index
    all_ids = from_here.index
    missing_ids = set(all_ids).difference(ids_to_remove)
    missing_df = from_here.loc[missing_ids]
    return missing_df


def zillowfy(df):
    """
    Add data from zillow if property was sold
    """
    completed_df = pd.DataFrame([])
    indexes_to_drop = []
    for index, data in df.iterrows():
        if 'zillow_id' in data and data['zillow_id']:
            # we already got data for this property, it was sold. No need to do anything else
            continue
        address = data['asset_address_content_1']
        zipcode = data['zipcode']
        summary = zillow.get_summary(address, zipcode)
        if summary.last_sold_date:
            last_sold_date = datetime.strptime(summary.last_sold_date, '%m/%d/%Y').date()
            if data['auction_end_date'] < last_sold_date:
                data['zillow_id'] = summary.zillow_id
                data['zestimate_amount'] = summary.zestimate_amount
                data['zestimate_valuation_range_high'] = summary.zestimate_valuation_range_high
                data['zestimate_valuation_range_low'] = summary.zestimate_valuationRange_low
                data['zillow_last_date_sold'] = last_sold_date
                data['zillow_lasl_sold_price'] = summary.last_sold_price
                completed_df.append(data, ignore_index=True)
                indexes_to_drop.append(index)

    df.drop(indexes_to_drop, inplace=True)
    return completed_df


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


if __name__ == "__main__":
    main('20190906_Alameda_1.html')

