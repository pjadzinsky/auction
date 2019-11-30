import os

COMPLETED_FOLDER = 'auction/completed'
URL_FOLDER = 'auction/urls'
ACTIVE_AUCTION_FOLDER = 'auction/active'
CANCELED_FOLDER = 'auction/canceled'
AUCTIONED_FOLDER = 'auction/auctioned'
UNKNOWN_FOLDER = 'auction/unknown'
WRONGFULY_DEACTIVE = 'auction/wrongfuly_deactivated'
ZILLOWED_FOLDER = 'auction/zillowed'
COUNTIES = ['Alameda', 'Contra Costa', 'Marin', 'Napa', 'Sacramento', 'San Francisco', 'San Joaquin',
            'San Mateo', 'Santa Clara', 'Santa Cruz', 'Solano', 'Sonoma', 'Stanislaus']
PROJ_ROOT = '/Users/pjadzinsky/PycharmProjects/auction'
URL_ATTRIBUTES = ["auction_id", "asset_address_content_1", "asset_address_content_2", "asset_auction_date",
                  "asset_auction_type", "asset_beds", "asset_baths", "asset_sqft", "label_after_repair_value_value",
                  "label_starting_bid_value", "asset_save_label", "asset_No Buyer's Premium_label", "asset_image",
                  "asset_Newly Listed_label", "asset_Broker Commission Available_label"]
KEYS_TO_EXTRACT = ['venue_code', 'venue_id', 'auction_date', 'auction_status', 'bid_count', 'venue_type',
                   'trustee_sale',
                   'online_event', 'interior_access', 'financing_available', 'cash_only',
                   'est_opening_bid', 'property_id', 'property_address', 'property_city',
                   'property_state_code', 'property_zip', 'lot_size', 'home_square_footage', 'bedrooms',
                   'baths', 'year_built', 'property_county', 'property_occupancy_status', 'occupancy_status',
                   'property_type', 'saved_count', 'estimated_value', 'opening_bid', 'est_debt', 'after_repair_value',
                   'propertyViews', 'status_label',
                   'street_name', 'city', 'county', 'postal_code']
REPLACE_LIST = {
    'postal_code': 'property_zip',
    'city': 'property_city',
    'county': 'property_county',
    'street_name': 'property_address',
}

COLUMNS = [
    'auction_id',
    'after_repair_value',
    'auction_date',
    'auction_status',
    'baths',
    'bedrooms',
    'bid_count',
    'cash_only',
    'est_opening_bid',
    'estimated_value',
    'financing_available',
    'home_square_footage',
    'href',
    'interior_access',
    'lot_size',
    'my_status',
    'occupancy_status',
    'online_event',
    'propertyViews',
    'property_address',
    'property_city',
    'property_county',
    'property_id',
    'property_occupancy_status',
    'property_state_code',
    'property_type',
    'property_zip',
    'saved_count',
    'status_label',
    'trustee_sale',
    'venue_code',
    'venue_id',
    'venue_type',
    'year_built',
]
LOGS = os.path.join(PROJ_ROOT, 'auction.log')
