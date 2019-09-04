"""
1. I generated html files in 'urls' by following 'gioloe' response here https://stackoverflow.com/questions/3314429/how-to-view-generated-html-code-in-firefox/3314453#3314453
    I found the element in the html that when I hover over, highlights the whole table of properties.
    Then copy pasted the html into 'urls' folder
2. Pass those files to parse_url.process_html_files(files)
    This step generates csv/<date>.csv with all data from auction.com
3. How do we know if auction finished succesfully? Call zillow to get estimated value/rents and
    once transaction closes the executed price

"""
from datetime import date, datetime, timedelta
import pandas as pd
import zillow
pd.set_option('max_columns', 25)

HALF_YEAR = timedelta(days=182)

def main():
    df = pd.read_csv('csv/20190902.csv', sep='\t')
    df.loc[:, 'auction_end_date'] = df['asset_auction_date'].apply(parse_date)
    print(df[['asset_auction_date', 'auction_end_date']])


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
    main()