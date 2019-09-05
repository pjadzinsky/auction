from html.parser import HTMLParser
import glob
import os

import pandas as pd
import re

from config import URL_FOLDER, AUCTION_FOLDER

pd.set_option('max_columns', 25)


class MyHTMLParser(HTMLParser):
    property_id = None
    column = None
    root_regex = re.compile('asset_[0-9]*_root')

    def __init__(self, df):
        HTMLParser.__init__(self)
        self.df = df

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.set_property_id(attrs)
            print('start tag "a" found', self.property_id)
        if tag in ['h4', 'label', 'div']:
            self.set_column(attrs)
        #print("Encountered a start tag:", tag, self.property_id, self.column)

    def handle_endtag(self, tag):
        #print("Encountered an end tag :", tag, self.property_id, self.column)
        pass

    def handle_data(self, data):
        if self.property_id:
            print("*" * 80)
            print(self.property_id, self.column, data)
            self.df.loc[self.property_id, self.column] = data
            print("*" * 80)
        #print("Encountered some data  :", data, self.property_id, self.column)

    def set_property_id(self, attrs):
        for attr, value in attrs:
            if self.root_regex.match(value):
                _, property_id_str, _ = value.split('_')
                self.property_id = int(property_id_str)
                return

    def set_column(self, attrs):
        # attrs is a list of tuples, seems like each list has 2 tuples, each tuple is a (key, value)
        for attr, value in attrs:
            if attr == 'data-elm-id':
                self.column = value.replace(str(self.property_id) + '_', '')
                break
        print('New column found:', self.column)


def process_html_files(df, date, files, output_name=None):
    if not output_name:
        output_name = os.path.join(AUCTION_FOLDER, '{}.csv'.format(date))

    parser = MyHTMLParser(df)
    for url_file in files:
        for line in open(url_file):
            parser.feed(line)
        print(parser.df.head())
        parser.df.to_csv(output_name)

    return output_name


def load_last_auction_df():
    all_csvs = glob.glob(os.path.join(AUCTION_FOLDER, '*.csv'))
    if all_csvs:
        last_csv = sorted(all_csvs)[-1]
        df = pd.read_csv(last_csv, index_col=0)
    else:
        df = pd.DataFrame([])
        df.index.name = 'auction_id'

    return df


def files_by_date(date):
    files = glob.glob(os.path.join(URL_FOLDER, '{}*.html'.format(date)))
    return files


if __name__ == "__main__":
    date = '20190901'
    df = load_last_auction_df()
    url_files = files_by_date(date)
    process_html_files(date, url_files)
