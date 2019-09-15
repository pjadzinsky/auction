from html.parser import HTMLParser
import json
#from tempfile import TemporaryDirectory
import glob
import pprint
import os
import time

import pandas as pd
import re

import config
from config import URL_FOLDER, ACTIVE_AUCTION_FOLDER, PROJ_ROOT, URL_ATTRIBUTES

pd.set_option('max_columns', 25)


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


'''
class MetadataParser(HTMLParser):
    column = None
    in_td = False

    def __init__(self):
        HTMLParser.__init__(self)
        self.s = pd.Series([])

    def set_auction_id(self, auction_id):
        self.s['auction_id'] = auction_id

    def clear_series(self):
        del self.s
        self.s = pd.DataFrame([])
        self.s.index.name = 'auction_id'

    def handle_starttag(self, tag, attrs):
        self.column = None
        if tag == 'td':
            self.in_td = True
        if self.in_td and tag == 'div':
            # extract data-elm-id inside tables starting with tag 'div'
            self.set_column(attrs)
        if not self.in_td and tag == 'h1':
            self.set_column(attrs)
        if not self.in_td and tag == 'div':
            self.set_column(attrs, limited_set=True)

    def handle_endtag(self, tag):
        if tag == 'td':
            self.in_td = False

    def handle_data(self, data):
        #if self.column in URL_ATTRIBUTES:
        if self.column:
            self.s[self.column] = data
            self.column = None

    def set_column(self, attrs, limited_set=False):
        # attrs is a list of tuples, seems like each list has 2 tuples, each tuple is a (key, value)
        # only keep those with 'data-elm-id' in the 'key' possition
        filtered = [(a, v) for a, v in attrs if a == 'data-elm-id']
        if filtered:
            attr, value = filtered[0]
            if limited_set and value not in [
                'property_header_address',
                'property_header_location',
                'arv_value',
                'est_credit_bid_value',
                'opening_bid_value',
                'estimated_debt_value',
            ]:
                pass
            else:
                self.column = value.replace(str(self.s['auction_id']) + '_', '')


'''

def extract_property_series(html_txt):
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

                """
                for key in keys:
                    if isinstance(d, dict):
                        if key in d:
                            d = d[key]
                        else:
                            return None
                s[key] = d
                return s
                """

            # below doesn't seem to work anymore as of 2019, Sep 14.
            # Initial dictory has keys:
            # 'verificationModalReducer', 'user', 'properties', 'modals', 'contracting', 'form', 'queues', 'bidding', 'message', 'featureFlags', 'biddingDeposit', 'propertyAnalytics', 'purchaseProfiles', 'finalOffer'])
            # Most of them are useless except:
            # properties    property info
            # contracting ? (is empty but might be good when in contract)

            extract_field(d, s, config.KEYS_TO_EXTRACT)
            break
    return s


def extract_all_data_elm_id(html):
    """ Quick tool to extract all strings associated with data-elm-id=<string> in html
    This is a general tool I'm using to learn crawling, nothing to do with auction.com in particular
    """
    found = []
    regex = re.compile('data-elm-id="([^"]*)"')
    for line in open(html):
        found.extend(regex.findall(line))

    found = [f for f in found if not (f.startswith('card_') or f.startswith('footer_') or f.startswith('chat')
                                      or f.startswith('save_') or f.startswith('property_card_') or f.startswith('property_image')
                                      or f.startswith('similar_') or f.startswith('comp_') or f.startswith('help_'))]
    pprint.pprint(found)

'''
class MyHTMLParser(HTMLParser):
    property_id = None
    column = None
    root_regex = re.compile('asset_[0-9]*_root')

    def __init__(self):
        HTMLParser.__init__(self)
        self.df = pd.DataFrame([])
        self.df.index.name = 'auction_id'

    def clear_df(self):
        del self.df
        self.df = pd.DataFrame([])
        self.df.index.name = 'auction_id'

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.set_property_id(attrs)
        if tag in ['h4', 'label', 'div']:
            self.set_column(attrs)

    def handle_endtag(self, tag):
        pass

    def handle_data(self, data):
        if self.column in URL_ATTRIBUTES:
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
'''


'''
def swap_labels(series):
    """
    # swap labels is no longer needed if we use extract_property_series
    
    When reading the table for each auction_id, we get 2 attributes that are related to each other. We get things like
    <str>_label and <str>_value, for example total_bedrooms_label and total_bedrooms_value with associted values of
    'Beds' and 2
    Here I'm changing from :
        total_bedrooms_label: 'Beds'
        total_bedrooms_value: 2

    to:
    Beds: 2
    :param series:
    :return:
    """
    label_indexes = [l for l in series.index if l.endswith('_label')]
    for label_index in label_indexes:
        value_index = label_index.replace('label', 'value')
        if value_index in series:
            new_index = series[label_index]
            new_value = series[value_index]
            series[new_index] = new_value
            series.drop([label_index, value_index], inplace=True)
'''


'''
def process_html_files(wildcard, basename, folder=os.path.join(PROJ_ROOT, URL_FOLDER)):
    url_files = files_by_date(wildcard, folder)
    #url_files = [f for f in url_files if 'Clara_1' in f]
    print('Converting {} files to csv'.format(len(url_files)))
    pprint.pprint(url_files)

    parser = MyHTMLParser()
    for url_file in url_files:
        t0 = time.time()
        for line in open(url_file):
            parser.feed(line)
        t1 = time.time()
        print('processing {} took {}s'.format(url_file, t1 - t0))

    df = parser.df
    output_name = os.path.join(PROJ_ROOT, ACTIVE_AUCTION_FOLDER, '{}.csv'.format(basename))
    df.to_csv(output_name)
    # extract parameters to their own columns: city, state, zipcode and county
    parse_city_state_zipcode_county(df)

    return df
'''


def files_by_date(wildcard, folder):
    files = glob.glob(os.path.join(folder, wildcard))
    return files

'''
def parse_city_state_zipcode_county(df):
    """
    # This method is no longer needed if we use extract_property_series
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
'''



if __name__ == "__main__":
    pd.set_option('max_rows', 100)
    pd.set_option('max_columns', 100)
    html = '/Users/pjadzinsky/PycharmProjects/auction/urls/test_property_page.html'
    for line in open(html):
        parser.feed(line)

    print(parser.s)
    print('*'*80)
    # swap labels is no longer needed if we use extract_property_series
    swap_labels(parser.s)
    print(parser.s)
    s = extract_property_series(html)
    print(s)

    #extract_all_data_elm_id(html)
    """
    wildcard = '20190907_Alameda_1.html'
    folder = URL_FOLDER
    t0 = time.time()
    df = process_html_files(wildcard, 'test')
    print('process_html_files took {}s'.format(time.time() - t0))
    print(df.groupby('county').count()['city'])
    print(df.shape)
    """
