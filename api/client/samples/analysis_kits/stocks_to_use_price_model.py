"""Sample API script for modeling prices based on the stocks-to-use ratio

This script creates a basic CME price valuation model for corn and soybeans
using the US stocks-to-use ratio. A Gro public display containing the data series
used in this exercise is linked here: 
https://app.gro-intelligence.com/displays/1jdOenVRw

The stocks-to-use ratio is calculated each month as reported in the USDA's PS&D
database. The price variable is defined as the monthly average 'new crop' 
(December futures for corn and November futures for soybeans) price for the 
relevant report month. For example, the corn-June scatterplot will compare the US
stocks-to-use ratio from all June reports relative to the corresponding monthly 
average December corn futures price.

The output of this script will be a PDF file for each modeled crop, saved in
the current working directory. Each PDF will have 13 pages in total, 
including a scatterplot for each report month as well as a 
scatterplot summarizing the entire sample.

"""

import os
import calendar

import pandas as pd

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from sklearn import linear_model

from api.client.gro_client import GroClient

API_HOST = 'api.gro-intelligence.com'
TOKEN    = os.environ['GROAPI_TOKEN']
client   = GroClient(API_HOST, TOKEN)

ref = {'corn':{'futures_contract_month':12},
       'soybeans':{'futures_contract_month':11}}

UNITED_STATES_REGION_ID = 1215

def contract_month_history(crop, contract_month):
    """full history of settlement prices for a specific commodity
    and month of expiry. e.g. December corn

    Parameters
    ----------
    crop : string
        'corn' or 'soybeans'
    contract_month : integer

    Returns
    -------
    pandas.Series
    """
    market = client.search_for_entity('items', crop)
    
    SETTLEMENT_PRICE = client.search_for_entity('metrics', 'futures prices settle (currency/mass)')
    client.add_single_data_series({'metric_id': SETTLEMENT_PRICE, 
                                   'item_id': market, 
                                   'region_id': 1215, 
                                   'source_id': 81,
                                   'start_date': '2006-01-01',
                                   'show_revisions': True})
    
    df = client.get_df().copy()
    df['reporting_date'] = pd.to_datetime(df['reporting_date'])
    
    px_df = df.loc[(df['metric_id'] == SETTLEMENT_PRICE) & \
                   (df['item_id'] == market) & \
                   (df['end_date'].dt.month == contract_month)].set_index('reporting_date')
    
    ct_grps   = px_df.groupby('end_date')
    contracts = ct_grps.groups.keys()
    contracts.sort()
    
    df_out = pd.concat([ct_grps.get_group(c)['value'] for c in contracts], 
                        sort=True, keys=contracts, axis=1)
    ts_out = df_out.fillna(method='bfill', axis=1).iloc[:,0]
    ts_out.name = 'price_history'
    
    return ts_out

def get_price(crop):
    """calculates monthly average new crop CME price    

    Parameters
    ----------
    crop : string
        'corn' or 'soybeans'
    
    Returns
    -------
    pandas.Series
    """
    ct_mon = ref[crop.lower()]['futures_contract_month']
    
    px_hist = contract_month_history(crop, ct_mon)
    ts_out  = px_hist.resample('M').mean().resample('D').fillna('bfill')
    ts_out.name = 'price'
    
    return ts_out

def get_stocks_to_use(crop, region=UNITED_STATES_REGION_ID):
    """Calculate historical carryout to use ratio for a given commodity  

    Parameters
    ----------
    crop : string
        'corn' or 'soybeans'
    Returns
    -------
    pandas.Series
    """
    crop_id = client.search_for_entity('items', crop)
    
    # add stocks series
    ENDING_STOCKS = client.search_for_entity('metrics', 'stocks, ending quantity (mass)')
    client.add_single_data_series({'metric_id': ENDING_STOCKS, 
                                   'item_id': crop_id, 
                                   'region_id': region, 
                                   'source_id': 14, 
                                   'frequency_id': 9, 
                                   'start_date': '2006-12-31',
                                   'show_revisions': True})    
    
    
    # add consumption series
    CONSUMPTION = client.search_for_entity('metrics', 'domestic consumption (mass)')
    client.add_single_data_series({'metric_id': CONSUMPTION, 
                                    'item_id': crop_id, 
                                    'region_id': region, 
                                    'source_id': 14, 
                                    'frequency_id': 9,
                                    'start_date': '2006-12-31',
                                    'show_revisions': True})

    df_pts = client.get_df().copy()
    df_pts = df_pts.sort_values('end_date', ascending=True)
    df_pts['reporting_date'] = pd.to_datetime(df_pts['reporting_date'])
    
    df_grp = df_pts.groupby(['item_id', 'metric_id', 'reporting_date']).last()
    
    stocks = df_grp.loc[(crop_id, ENDING_STOCKS), :]['value']
    cons   = df_grp.loc[(crop_id, CONSUMPTION), :]['value']
    
    ts_out = stocks.div(cons)
    ts_out.name = 'stocks_to_use'
    
    return ts_out

def run_regression(df):
    """run linear regression between stocks to use ratio and price  

    Parameters
    ----------
    df : pandas.DataFrame

    Returns
    -------
    float, float, float
        r-squared value, intercept, and x variable coefficient
    """
    lm = linear_model.LinearRegression()
    X  = df.loc[:, ['stocks_to_use']]
    
    lm.fit(X, df['price'])
    
    rsq = lm.score(X, df['price'])
    
    return rsq, lm.intercept_, lm.coef_[0]

def create_scatterplot(df_in, name, crop):
    """scatterplot vizualization for regression model

    Parameters
    ----------
    df_in : string
        'corn' or 'soybeans'
    name : int or string
        month of report being analyzed or 'all' for all months
    crop : string
        'corn' or 'soybeans'
    """    
    stu = df_in['stocks_to_use']
    px  = df_in['price']
    
    rsq, intercept, slope = run_regression(df_in)
    
    fig = plt.figure(figsize=(5, 5), dpi=300)
    ax  = fig.add_subplot(111)

    line = slope * stu.values + intercept
    
    if (type(name) is str):
        mon = name
    else:
        mon = calendar.month_abbr[name]
    
    ttl = '{}: {} Reports: rsq:{}'.format(crop.title(), mon, rsq.round(2))
    
    lbl = 'y={:.2f}x+{:.2f}'.format(slope, intercept)
    plt.plot(stu.values, line, 'r', label=lbl)

    plt.scatter(stu.values, px.values, color="k", s=3.5)
    plt.legend(fontsize=9)

    fig.suptitle(ttl, fontsize=12)
    ax.set_xlabel('Stocks to Use Ratio')
    ax.set_ylabel('Price')

    plt.close()

    return fig
    
def write_price_model(crop):
    """run a regression between price and stocks to use for all WASDE report months,
       create a scatterplot of regression values, and write to PDF

    Parameters
    ----------
    crop : string
        'corn' or 'soybeans'

    """
    stu = get_stocks_to_use(crop)
    px  = get_price(crop)
    df  = pd.concat([stu, px], axis=1).dropna()
    
    grp = df.groupby(df.index.month)
        
    fig_lst = [create_scatterplot(df, 'All', crop)]
    fig_lst.extend([create_scatterplot(group, name, crop) for name, group in grp])

    fn = os.path.join(os.getcwd(), '{}.pdf'.format(crop))
    pp = PdfPages(fn)
    for f in fig_lst: pp.savefig(f)
    pp.close()
    
if __name__ == "__main__":
    write_price_model('corn')
    write_price_model('soybeans')