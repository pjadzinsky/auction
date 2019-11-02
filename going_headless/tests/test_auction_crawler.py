import os
import unittest

from auction import auction_crawler


class TestClass(unittest.TestCase):
    def test_1(self):
        html = os.path.join('data', '2807564.html')
        data = auction_crawler.extract_property_series(html)
        assert data['my_status'] == 'active'

    def test_2(self):
        html = os.path.join('data', '2839753.html')
        data = auction_crawler.extract_property_series(html)
        print(data['my_status'])
        #assert data['my_status'] == 'canceled'

    def test_for_sale(self):
        html = os.path.join('data', '2663728.html')
        data = auction_crawler.extract_property_series(html)
        assert data['my_status'] == 'canceled'

    def test_reverted_to_beneficiary(self):
        html = os.path.join('data', '2844454.html')
        data = auction_crawler.extract_property_series(html)
        assert data['my_status'] == 'canceled'

    def test_active_scheduled_for_auction(self):
        html = os.path.join('data', '2850469.html')
        data = auction_crawler.extract_property_series(html)
        assert data['my_status'] == 'active'

    def test_active(self):
        html = os.path.join('data', '2799446.html')
        data = auction_crawler.extract_property_series(html)
        print(data['my_status'])
        #assert data['my_status'] == 'active'
