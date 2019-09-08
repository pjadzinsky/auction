Idea:

I still have to extract a few fields that are very important. One of them is 'vacant'. Unfortunately this
is not displayed in the summary and seems like the only way to get whether a property is vacant is to click
on it. I think there aren't soo many properties being added on a weekly basis so I should change logic to be:

* get previous properties being auction
* get current properties being auction
* for new properties, open the property specific page and pull all relevant data.

September 07, 2019

I changed code to use a crawler. However the crawler now gets the whole html (rather than the the 'asset_list')
and now I had to fix the fields that are extracted onto the CSV (see config.URL_ATTRIBUTES)

Before September 07, 2019

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

