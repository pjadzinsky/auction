import os

COMPLETED_FOLDER = 'completed'
URL_FOLDER = 'urls'
ACTIVE_AUCTION_FOLDER = 'active_auction'
PENDING_TRANSACTION_FOLDER = 'pending_transaction'
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
                   'propertyViews', 'status_label']
LOGS = os.path.join(PROJ_ROOT, 'auction.log')
