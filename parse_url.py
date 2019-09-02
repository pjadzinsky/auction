from html.parser import HTMLParser
import pandas as pd
import re

pd.set_option('max_columns', 25)

class MyHTMLParser(HTMLParser):
    property_id = None
    column = None
    root_regex = re.compile('asset_[0-9]*_root')
    df = pd.DataFrame([])

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


if __name__ == "__main__":
    url_file = '/Users/pjadzinsky/PycharmProjects/auction/urls/20190901_mountain_view.html'
    parser = MyHTMLParser()
    print(1)
    for line in open(url_file):
        parser.feed(line)
    print(parser.df.head())
    parser.df.to_csv('/tmp/url.csv')
