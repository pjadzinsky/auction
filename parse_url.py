from html.parser import HTMLParser
import glob
import os

import pandas as pd
import re

from config import URL_FOLDER, ACTIVE_AUCTION_FOLDER, PROJ_ROOT

pd.set_option('max_columns', 25)


class MyHTMLParser(HTMLParser):
    property_id = None
    column = None
    root_regex = re.compile('asset_[0-9]*_root')
    df = pd.DataFrame([])
    df.index.name = 'auction_id'

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.set_property_id(attrs)
        if tag in ['h4', 'label', 'div']:
            self.set_column(attrs)

    def handle_endtag(self, tag):
        pass

    def handle_data(self, data):
        if self.property_id:
            self.df.loc[self.property_id, self.column] = data

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


def process_html_files(wildcard, basename, folder=os.path.join(PROJ_ROOT, URL_FOLDER)):
    url_files = files_by_date(wildcard, folder)
    output_name = os.path.join(PROJ_ROOT, ACTIVE_AUCTION_FOLDER, basename)

    parser = MyHTMLParser()
    for url_file in url_files:
        for line in open(url_file):
            parser.feed(line)
        parser.df.to_csv(output_name)

    df = parser.df
    # extract parameters to their own columns: city, state, zipcode and county
    parse_city_state_zipcode_county(df)

    return df


def load_last_df(folder):
    all_csvs = glob.glob(os.path.join(folder, '*.csv'))
    if all_csvs:
        last_csv = sorted(all_csvs)[-1]
        df = pd.read_csv(last_csv, index_col=0)
    else:
        df = pd.DataFrame([])
        df.index.name = 'auction_id'

    return df


def files_by_date(wildcard, folder):
    files = glob.glob(os.path.join(folder, wildcard))
    return files


def parse_city_state_zipcode_county(df):
    """
    In place, extract 'city', 'state', 'zipcode' and 'county' from 'asset_address_content_2'

    :param df:
    :return:
    """
    for index, auction in df.iterrows():
        city, state_zipcode, county = auction.asset_address_content_2.split(',')
        state, zipcode = state_zipcode.split()
        df.loc[index, 'city'] = city
        df.loc[index, 'state'] = state
        df.loc[index, 'zipcode'] = zipcode
        df.loc[index, 'county'] = county.replace(' County', '')



if __name__ == "__main__":
    wildcard = '20190907_Alameda_1.html'
    folder = URL_FOLDER
    df = process_html_files(wildcard, 'test')
    print(df.groupby('county').count()['city'])
    df.to_csv(os.path.join(ACTIVE_AUCTION_FOLDER),)
    print(df.shape)
