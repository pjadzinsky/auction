Sep 14, 2019

There are different Crawling steps
1. gets all the auction_ids of properties actively being auctioned (and the html to the specific page)
2. gets the dataframe of properties already identified in the past as being active
3. computes the set of auction_ids that are in 1. but not in 2. (this are new property_ids)
4. for each auction id in 3, it gets into url identified in 1 and extracts property info. At this point
    we can save the 
5. computes a set of auctions_ids that are in 2. but not in 1. This are removed property_ids from 
    auction.com. These properties could have been removed because auction was canceled or it was conducted.
    Either way we have to get information on these. If status is 'Pending', we have to add it to list
    of properties to be zillowfied. Regardless of whether status is 'Pending'/'canceled' (don't know 
    how they show that info) we have to remove these properties from ACTIVE_AUCTION_FOLDER.
    
All the info I have so far is in a different format. To hack it I could get all the IDS of auctions
(regardless of status) and do it semi-manually. 

September 07, 2019

I changed code to use a crawler. However the crawler now gets the whole html (rather than the the 'asset_list')
and now I had to fix the fields that are extracted onto the CSV (see config.URL_ATTRIBUTES)

Before September 07, 2019

# crawler
## important: versions
I started with chromedriver 77.0.3865.40 and Chrome Canary 78.0.3899.0 and it worked fine but at some point
OS updated my Chrome Canary to 79 and I couldn't find a chromedriver that matches (probably will be uploaded
soon).
I started by following this post: 
https://duo.com/decipher/driving-headless-chrome-with-python
Downloaded driver from https://chromedriver.chromium.org/downloads


# manually
 I started by following this by 'gioloe' response here https://stackoverflow.com/questions/3314429/how-to-view-generated-html-code-in-firefox/3314453#3314453
 I found the element in the html that when I hover over, highlights the whole table of properties ('asset_list')
 Now I have to extract the different fields from the table
 address, city, zipcode, auction date, auction type, num_rooms, num_baths, est. resale value, opening_bid
 searching for 'data-elm-id' I found the following vaues
 
* asset_2654221_root
* asset_2654221_image
* asset_<number>_address_content_1: address
* asset_<number>_address_content_2: city, zipcode
* asset_2770278_auction_date
* asset_2654221_auction_type
* asset_2654221_beds
* asset_2654221_baths
* asset_2654221_sqft
* asset_2654221_toggle_save
* asset_2654221_No Buyer's Premium
* asset_2654221_No Buyer's Premium_label
* label_after_repair_value
* label_after_repair_value_value
* label_reserve
* label_reserve_value
* label_starting_bid
* label_starting_bid_value

