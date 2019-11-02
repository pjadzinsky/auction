import pandas as pd
import numpy as np

from config import ZILLOWED_FOLDER
from auction import load_last_df

pd.set_option('max_columns', 25)


def main():
    df, _ = load_last_df(ZILLOWED_FOLDER)

    df.drop(['saved_count', 'property_state_code', 'venue_type', 'trustee_sale',
             'zillow_id', 'venue_code', 'venue_id', 'financing_available', 'property_id'], axis=1, inplace=True)

    merge_estimates(df)
    print(df.columns)
    df.loc[:, 'sold_to_estimated_ratio'] = df.zillow_last_sold_price / df.after_repair_value
    df.sort_values(by='sold_to_estimated_ratio', inplace=True)

    selected_columns = [
        'sold_to_estimated_ratio', 'after_repair_value', 'online_event', 'status_label'
    ]
    print(df[selected_columns])


def merge_estimates(df):
    df.loc[:, 'after_repair_value'] = df.after_repair_value.apply(lambda x: np.nan if x == "Not Available" else int(x))
    df.loc[:, 'after_repair_value'] = df[['after_repair_value', 'zestimate_amount', 'estimated_value']].apply(
        lambda x: np.nanmin(x), axis=1
    )


if __name__ == "__main__":
    main()