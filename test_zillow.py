from pyzillow.pyzillow import ZillowWrapper, GetDeepSearchResults


if __name__ == "__main__":
    with open('/Users/pjadzinsky/.zillow') as f:
        key = f.read().replace('\n', '')
    zillow_data = ZillowWrapper(key)

    response = zillow_data.get_deep_search_results('2135 Greer Rd', 94303)
    result = GetDeepSearchResults(response)
    print(result.__dict__)

