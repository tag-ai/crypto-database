"""
coin_list_update.py

Get the top coins by market cap, and update master list
to use for twitter scrape. Run this daily.

Author: Alex Galea

"""
import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
import time
import datetime
sys.path.append('../utils')
from config import load_config
SCRIPT_NAME = 'twitter_coin_list_update'
DATE = datetime.datetime.utcnow()
DATE_STR = DATE.strftime('%Y-%m-%d')
config = load_config(var_type='globals', script=SCRIPT_NAME)

# Convert to absolute file paths
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
def absolute_path(path) -> str:
    return path if os.path.isabs(path) else os.path.join(DIR_PATH, path)
config['DATA_PATH'] = absolute_path(config['DATA_PATH'])


def update_filestore(df, output_search_terms_file):
    # Configure local filestore
    base_path = os.path.join(config['DATA_PATH'],
                             os.path.split(output_search_terms_file)[0])
    if not os.path.exists(base_path):
        os.makedirs(base_path)

    # Save top coins
    f_name = os.path.join(
        base_path,
        'historical',
        '{}_top_coins.csv'.format(DATE_STR))
    f_path = os.path.split(f_name)[0]
    if not os.path.exists(f_path):
        os.makedirs(f_path)
    df[df['rank'] <= config['NUM_TOP_COINS']].to_csv(f_name, index=False)

    # Update master list with top coins
    f_name = output_search_terms_file
    if os.path.exists(f_name):
        print('Master list found at {}, updating'.format(f_name))
        # Load the old list
        df_prev = pd.read_csv(f_name)
        df_prev['rank'] = float('nan')  # we'll update this
        # Merge in new data
        df_concat = pd.concat((df[df['rank'] <= config['NUM_TOP_COINS']], df_prev))
        mask_drop_dups = ~(df_concat[['symbol', 'name']].duplicated()) # important to do this
                                                                       # before sorting, so we
                                                                       # drop from df_prev
        df_concat = df_concat[mask_drop_dups].sort_values('rank')
    else:
        print('No master list found at {}, writing new one'.format(f_name))
        df_concat = df[df['rank'] <= config['NUM_TOP_COINS']].sort_values('rank')

    # Save master list
    df_concat.to_csv(f_name, index=False)

    # Save master list to historical
    f_name = os.path.join(
        base_path,
        'historical',
        '{}_{}'.format(DATE_STR, os.path.split(output_search_terms_file)[-1]))
    f_path = os.path.split(f_name)[0]
    if not os.path.exists(f_path):
        os.makedirs(f_path)
    df_concat.to_csv(f_name, index=False)


def update_coin_master_list(output_search_terms_file):
    # Get top coins by market cap
    top_coins = []
    for start in [1, 101, 201, 301, 401, 501, 601, 701, 801, 901,
                  1001, 1101, 1201, 1301, 1401, 1501, 1601, 1701, 1801, 1901,
                  2001, 2101, 2201, 2301, 2401, 2501, 2601, 2701, 2801, 2901]:
        if start > config['NUM_TOP_COINS']:
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

    update_filestore(df, output_search_terms_file)


if __name__ == '__main__':
    args = load_config(var_type='args', script=SCRIPT_NAME)
    update_coin_master_list(**args)
