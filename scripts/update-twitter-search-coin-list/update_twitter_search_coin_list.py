"""
update_coin_master_list.py

Get the top coins by market cap, and update master list
to use for twitter scrape. Run this daily.

Author: Alex Galea

"""
import pandas as pd
import requests
from bs4 import BeautifulSoup
import click
import os
import time
import datetime
DATA_PATH = '../../data/' # WARNING: do not change this variable - will break twitter-search
DATE = datetime.datetime.now()
DATE_STR = datetime.datetime.now().strftime('%Y-%m-%d')
NUM_TOP_COINS = 100

# Convert to absolute file paths
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
DATA_PATH = DATA_PATH if os.path.isabs(DATA_PATH)\
            else os.path.join(DIR_PATH, DATA_PATH)

def update_filestore(df, data_path):
    _out_path = DATA_PATH if not data_path else data_path

    # Save top coins
    f_name = os.path.join(
        _out_path,
        'coin-twitter-list',
        'historical',
        '{}_top_coins.csv'.format(DATE_STR))
    f_path = os.path.split(f_name)[0]
    if not os.path.exists(f_path):
        os.makedirs(f_path)
    df[df['rank'] <= NUM_TOP_COINS].to_csv(f_name, index=False)

    # Update master list with top coins
    f_name = os.path.join(
        _out_path,
        'coin-twitter-list',
        'coin_master_list.csv')
    if os.path.exists(f_name):
        print('Master list found at {}, updating'.format(f_name))
        # Load the old list
        df_prev = pd.read_csv(f_name)
        df_prev['rank'] = float('nan')  # we'll update this
        # Merge in new data
        df_concat = pd.concat((df[df['rank'] <= NUM_TOP_COINS], df_prev))
        mask_drop_dups = ~(df_concat[['symbol', 'name']].duplicated()) # important to do this
                                                                       # before sorting, so we
                                                                       # drop from df_prev
        df_concat = df_concat[mask_drop_dups].sort_values('rank')
    else:
        print('No master list found at {}, writing new one'.format(f_name))
        df_concat = df[df['rank'] <= NUM_TOP_COINS].sort_values('rank')

    # Save master list
    df_concat.to_csv(f_name, index=False)

    # Save master list to historical
    f_name = os.path.join(
        _out_path,
        'coin-twitter-list',
        'historical',
        '{}_coin_master_list.csv'.format(DATE_STR))
    f_path = os.path.split(f_name)[0]
    if not os.path.exists(f_path):
        os.makedirs(f_path)
    df_concat.to_csv(f_name, index=False)

    # Make copy of master list in DATA_PATH dir (needed by twitter-search)
    f_name = os.path.join(
        DATA_PATH,
        'coin-twitter-list',
        'coin_master_list.csv')
    f_path = os.path.split(f_name)[0]
    if not os.path.exists(f_path):
        os.makedirs(f_path)
    df_concat.to_csv(f_name, index=False)



@click.command()
@click.option(
    '--data-path',
    help='Folder to save historical data in.'
)
def update_coin_master_list(data_path):
    # Get top coins by market cap
    top_coins = []
    for start in [1, 101, 201, 301, 401, 501, 601, 701, 801, 901,
                  1001, 1101, 1201, 1301, 1401, 1501, 1601, 1701, 1801, 1901,
                  2001, 2101, 2201, 2301, 2401, 2501, 2601, 2701, 2801, 2901]:
        if start > NUM_TOP_COINS:
            break
        url = 'https://api.coinmarketcap.com/v2/ticker/?start={}&limit=100'
        print(url.format(start))
        page = requests.get(url.format(start))
        time.sleep(3)
        data = page.json()
        coins = [[d['rank'], d['symbol'], d['name']]
                 for _, d in data['data'].items()]
        top_coins += coins

    # Load into dataframe
    df = pd.DataFrame(top_coins, columns=['rank', 'symbol', 'name'])\
            .sort_values('rank')
    print('Loaded {} rows'.format(len(df)))

    update_filestore(df, data_path)


if __name__ == '__main__':
    update_coin_master_list()
