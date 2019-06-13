"""
Sample Gro API Client script for regressing stocks-to-use ratios vs price

This script creates a basic CME price valuation model using the US stocks-to-use ratio.
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

ref = {'corn':{'id':274, 'futures_contract_month':12},
       'soybeans':{'id':270, 'futures_contract_month':11}}

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

    market = ref[crop.lower()]['id']
    
    client = GroClient(API_HOST, TOKEN)
    
    client.add_single_data_series({'metric_id': 15820065, 
                                   'item_id': market, 
                                   'region_id': 1215, 
                                   'source_id': 81,
                                   'start_date': '2000-01-01',
                                   'show_revisions': True})
    
    df    = client.get_df()
    df['reporting_date'] = pd.DatetimeIndex(df['reporting_date'])
    df = df.set_index('reporting_date')
    df_ct = df[df['end_date'].dt.month == contract_month]
    
    ct_grps   = df_ct.groupby('end_date')
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

def get_ending_stocks(crop, region=1215):
    """Find USDA PS&D's end of marketing year inventory series     

    Parameters
    ----------
    crop : string
        'corn' or 'soybeans'
    region : int
        Gro region id
    Returns
    -------
    pandas.Series
    """
    
    c_ref   = ref[crop.lower()]
    crop_id = c_ref['id']

    client = GroClient(API_HOST, TOKEN)
    
    client.add_single_data_series({'metric_id': 1470032, 
                                   'item_id': crop_id, 
                                   'region_id': region, 
                                   'source_id': 14, 
                                   'frequency_id': 9, 
                                   'show_revisions': True})
    
    df_pts = client.get_df()
    df_pts = df_pts.sort_values('end_date', ascending=True)
    df_pts['report_date'] = pd.to_datetime(df_pts['reporting_date'])
    df_grp = df_pts.groupby('report_date').last()
    
    ts_out = df_grp['value']
    ts_out.name = 'stocks'
    
    return ts_out

def get_consumption(crop, region=1215):
    """Find USDA PS&D's domestic consumption series     

    Parameters
    ----------
    crop : string
        'corn' or 'soybeans'
    region : int
        Gro region id
    Returns
    -------
    pandas.Series
    """
    c_ref   = ref[crop.lower()]
    crop_id = c_ref['id']
    
    client = GroClient(API_HOST, TOKEN)
    
    client.add_single_data_series({'metric_id': 1480032, 
                                    'item_id': crop_id, 
                                    'region_id': region, 
                                    'source_id': 14, 
                                    'frequency_id': 9,
                                    'show_revisions': True})

    df_pts = client.get_df()
    df_pts = df_pts.sort_values('end_date', ascending=True)
    df_pts['report_date'] = pd.to_datetime(df_pts['reporting_date'])
    df_grp = df_pts.groupby('report_date').last()
    
    ts_out = df_grp['value']
    ts_out.name = 'use'
    
    return ts_out

def get_stocks_to_use(crop):
    """Calculate historical US carryout to use ratio for a given commodity  

    Parameters
    ----------
    crop : string
        'corn' or 'soybeans'
    Returns
    -------
    pandas.Series
    """
    united_states = 1215
    
    # model is based on US ending stocks and consumption
    stocks = get_ending_stocks(crop, region=united_states)
    cons   = get_consumption(crop, region=united_states)
    
    df_tot = pd.concat([stocks, cons], axis=1)
   
    ts_out = df_tot['stocks'].div(df_tot['use'])
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
    X  = df.loc[:,['stocks_to_use']]
    
    lm.fit(X, df['price'])
    
    rsq = lm.score(X,df['price'])
    
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
    ax.set_xlabel('Stocks to Use')
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
    