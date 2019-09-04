from pyzillow.pyzillow import ZillowWrapper, GetDeepSearchResults

def get_summary(address, zipcode):
    with open('/Users/pjadzinsky/.zillow') as f:
        key = f.read().replace('\n', '')
    zillow_data = ZillowWrapper(key)

    response = zillow_data.get_deep_search_results(address, zipcode)
    result = GetDeepSearchResults(response)
    return result

if __name__ == "__main__":
    result = get_summary('2135 Greer Rd', 94303)
    print(result.__dict__)
