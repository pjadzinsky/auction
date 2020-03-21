import holoviews as hv
import numpy as np
import pandas as pd
from datetime import datetime

from auction.config import ZILLOWED_FOLDER

pd.set_option('max_columns', 25)
#renderer = hv.renderer('bokeh')


def main(df):
    """

    :param df: output of load_last_df(ZILLOWED_FOLDER)
    :return:
    """
    add_columns(df)

    layout = hv.Layout()
    layout += scatter_plot_1(df)
    layout += scatter_plot_2(df)
    layout += scatter_plot_3(df)
    layout += scatter_plot_4(df)
    #renderer.save(layout.cols(1), '/tmp/scatter_layouts')


def add_columns(df):
    df.drop(['saved_count', 'property_state_code', 'venue_type', 'trustee_sale',
             'zillow_id', 'venue_code', 'venue_id', 'financing_available', 'property_id'], axis=1, inplace=True)

    merge_estimates(df)
    df.loc[:, 'sold_to_estimated_ratio'] = df.zillow_last_sold_price / df.after_repair_value
    df.loc[:, 'estimated_to_sold_diff'] = df.after_repair_value - df.zillow_last_sold_price
    df.sort_values(by='sold_to_estimated_ratio', inplace=True)


def scatter_plot_1(df):
    """ Produce a scatter plot of
    'zillow_last_date_sold' vs 'sold_to_estimated_ratio'
    """
    kdims = ['zillow_last_date_sold', ]
    vdims = ['sold_to_estimated_ratio', 'zillow_last_sold_price']
    data = hv.Dataset(df, kdims, vdims)
    crv = hv.HLine(1)
    crv *= data.to(hv.Scatter, 'zillow_last_date_sold', 'sold_to_estimated_ratio')
    crv.opts({
        'HLine': {'color': 'black', 'line_width': 1, 'alpha': 0.5},
    })
    return crv


def scatter_plot_3(df):
    """ Produce a scatter plot of 
    'zillow_last_sold_price' vs 'sold_to_estimated_ratio'
    """
    kdims = ['zillow_last_sold_price']
    vdims = ['sold_to_estimated_ratio']
    data = hv.Dataset(df, kdims, vdims)
    crv = data.to(hv.Scatter, 'zillow_last_sold_price', 'sold_to_estimated_ratio')
    crv *= hv.HLine(1)
    crv.opts({
        'HLine': {'color': 'black', 'line_width': 1, 'alpha': 0.5},
    })
    return crv


def scatter_plot_2(df):
    """ Produce a scatter plot of
    'expected_gain' vs 'date'
    """
    kdims = ['zillow_last_date_sold']
    vdims = ['estimated_to_sold_diff']
    data = hv.Dataset(df, kdims, vdims)
    crv = data.to(hv.Scatter, 'zillow_last_date_sold', 'estimated_to_sold_diff')
    crv *= hv.HLine(0)
    crv *= hv.HLine(1E5)
    crv *= hv.HLine(2E5)
    crv.opts({
        'HLine': {'color': 'black', 'line_width': 1, 'alpha': 0.5},
    })
    return crv


def scatter_plot_4(df):
    """ Produce a scatter plot of
    'expected_gain' vs 'date'
    """
    kdims = ['zillow_last_sold_price']
    vdims = ['estimated_to_sold_diff']
    data = hv.Dataset(df, kdims, vdims)
    crv = data.to(hv.Scatter, 'zillow_last_sold_price', 'estimated_to_sold_diff')
    crv *= hv.HLine(0)
    crv *= hv.HLine(1E5)
    crv *= hv.HLine(2E5)
    crv.opts({
        'HLine': {'color': 'black', 'line_width': 1, 'alpha': 0.5},
    })
    return crv


def merge_estimates(df):
    df.loc[:, 'after_repair_value'] = df.after_repair_value.apply(lambda x: np.nan if x == "Not Available" else int(x))
    df.loc[:, 'after_repair_value'] = df[['after_repair_value', 'zestimate_amount', 'estimated_value']].apply(
        lambda x: np.nanmin(x), axis=1
    )

