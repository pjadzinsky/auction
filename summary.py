import holoviews as hv
import numpy as np
import pandas as pd
from datetime import datetime, date


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
    df.loc[:, 'zillow_last_date_sold'] = df.zillow_last_date_sold.apply(lambda x:
                                                                        datetime.strptime(x, '%m/%d/%Y').date())

    selected_columns = [
        'sold_to_estimated_ratio', 'after_repair_value', 'online_event', 'status_label'
    ]
    print(df[selected_columns])
    scatter_plot_1(df)
    scatter_plot_2(df)


def scatter_plot_1(df):
    """ Produce a scatter plot of
    'zillow_last_date_sold' vs 'sold_to_estimated_ratio'
    """
    kdims = ['zillow_last_date_sold', ]
    vdims = ['sold_to_estimated_ratio', 'zillow_last_sold_price']
    data = hv.Dataset(df, kdims, vdims)
    renderer = hv.renderer('bokeh')
    crv = data.to(hv.Scatter, 'zillow_last_date_sold', 'sold_to_estimated_ratio')
    renderer.save(crv, '/tmp/scatter_1')


def scatter_plot_2(df):
    """ Produce a scatter plot of 
    'zillow_last_sold_price' vs 'sold_to_estimated_ratio'
    """
    kdims = ['zillow_last_sold_price']
    vdims = ['sold_to_estimated_ratio']
    data = hv.Dataset(df, kdims, vdims)
    renderer = hv.renderer('bokeh')
    crv = data.to(hv.Scatter, 'zillow_last_sold_price', 'sold_to_estimated_ratio')
    renderer.save(crv, '/tmp/scatter_2')


def merge_estimates(df):
    df.loc[:, 'after_repair_value'] = df.after_repair_value.apply(lambda x: np.nan if x == "Not Available" else int(x))
    df.loc[:, 'after_repair_value'] = df[['after_repair_value', 'zestimate_amount', 'estimated_value']].apply(
        lambda x: np.nanmin(x), axis=1
    )


if __name__ == "__main__":
    main()