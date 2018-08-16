"""
twitter_search.py

Search from yesterday at midnight UTC time, up until the previous ID
(in latest_tweet_id.txt) is reached. It iterated backwards and updates
max_id to find new tweets. This process is run twice to help ensure
no tweets are missed.

- https://developer.twitter.com/en/docs/tweets/search/api-reference/get-search-tweets

Author: Alex Galea

"""
import tweepy
from tweepy import OAuthHandler
from pymongo import MongoClient
from tqdm import tqdm
import json
import pandas as pd
import json
import datetime
import time
import os
import shutil
import sys
sys.path.append('../utils')
from data_writer import DataWriter
from emailer import send_email
from config import load_config
SCRIPT_NAME = 'twitter'
DATE = datetime.datetime.utcnow()
DATE_STR = DATE.strftime('%Y-%m-%d')
TWITTER_DATE_FORMAT = '%a %b %d %H:%M:%S +0000 %Y'
config = load_config(var_type='globals', script=SCRIPT_NAME)

# Convert to absolute file paths
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
def absolute_path(path) -> str:
    return path if os.path.isabs(path) else os.path.join(DIR_PATH, path)
config['DATA_PATH'] = absolute_path(config['DATA_PATH'])
config['API_KEY_FILE'] = absolute_path(config['API_KEY_FILE'])


def load_api():
    """
    Authorize the user and load the twitter API
    """
    with open(config['API_KEY_FILE'], 'r') as f:
        s = json.load(f)

    consumer_key = s['consumer_key']
    consumer_secret = s['consumer_secret']
    access_token = s['access_token']
    access_secret = s['access_secret']
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_secret)
    
    # Load the twitter API via tweepy
    return tweepy.API(auth)


# def filter_tweet(tweet):
#     tweet_fields = ['created_at', 'coordinates', 'id', 'full_text',
#                     'favorite_count', 'retweet_count', 'entities',
#                     'lang', 'user']
#     user_fields = ['created_at', 'verified', 'description',
#                    'friends_count', 'followers_count',
#                    'id', 'screen_name', 'favourites_count']

#     tweet = {k: v for k, v in tweet.items() if k in tweet_fields}
#     if 'user' in tweet_fields:
#         tweet['user'] = {k: v for k, v in tweet['user'] if k in user_fields}
#     return tweet


def get_since_id(term):
    """
    Read the previous tweet ID from a csv file.
    """
    prev_id_path = os.path.join(config['DATA_PATH'], 'tweets')
    if not os.path.exists(prev_id_path):
        os.makedirs(prev_id_path)
    prev_id_file_path = os.path.join(prev_id_path, 'last_coin_ids.json')

    if not os.path.isfile(prev_id_file_path):
        since_id = str(0)
    else:
        with open(prev_id_file_path, 'r') as f:
            # Load the starting ID (the last one we saved)
            # If not found, then set max_id = 0 to search
            # from first ID
            since_id = json.load(f).get(term, 0)
    print('Since ID = {}'.format(since_id))
    return since_id


def dump_since_ids(since_ids):
    """
    Read the previous tweet ID from a csv file.
    """
    prev_id_path = os.path.join(config['DATA_PATH'], 'tweets')
    if not os.path.exists(prev_id_path):
        os.makedirs(prev_id_path)
    prev_id_file_path = os.path.join(prev_id_path, 'last_coin_ids.json')

    if os.path.exists(prev_id_file_path):
        with open(prev_id_file_path, 'r') as f:
            # Load the previous IDs
            data = json.load(f)
    else:
        data = {}
    for term, _id in since_ids.items():
        data[term] = _id
    f_path = os.path.split(prev_id_file_path)[0]
    if f_path:
        if not os.path.exists(f_path):
            os.makedirs(f_path)
    with open(prev_id_file_path, 'w') as f:
        # Write the updated data
        json.dump(data, f)
    print('Dumped new prev IDs:')
    print(since_ids)


def term_to_filepath(term):
    # Remove illigal characters from file name
    return (''.join(x if (x.isalnum() or x in ' ._- ')
            else '_' for x in term)).lower()


def read_search_terms(search_terms_file, search_terms_col):
    search_terms_file = os.path.join(config['DATA_PATH'], search_terms_file)
    if not os.path.exists(search_terms_file):
        raise ValueError('Missing search terms file, expected at file path: {}'.format(search_terms_file))

    try:
        df = pd.read_csv(search_terms_file)
    except Exception as e:
        print('Error reading CSV file {}'.format(search_terms_file))
        raise e
    if search_terms_col not in df.columns:
        raise ValueError('{} not in {}. Bad value for search_terms_col argument'\
                        .format(search_terms_col, df.columns))
    return df[search_terms_col].values


def check_rate_limit(api):
    """
    Checks the rate limit status and returns the amount of time
    needed to wait (in seconds). If not at limit then return 0.
    """
    data = api.rate_limit_status()
    reset_time = datetime.datetime.fromtimestamp(
            data['resources']['search']['/search/tweets']['reset']
        )
    time_diff = reset_time - datetime.datetime.now()
    return (reset_time - datetime.datetime.now()).seconds


def log_errors(e, errors, max_errors,
               api, term, query, until_date, since_id,
               save_freq, local_filestore, num_iterations,
               testing_mode):
    """
    Log errors to file errors.log and prints them to screen.
    If called more 5 times, return break status for out of scope loop.
    """
    # Write to file
    with open(os.path.join(DIR_PATH, 'errors.log'), 'a+') as f:
        f.write('Exception raised in tweet_search.\n')
        f.write('Dumping vars:\n')
        for name, var in zip('api, query, until_date, since_id, save_freq, local_filestore, num_iterations'.split(', '),
                            [api, query, until_date, since_id, save_freq, local_filestore, num_iterations]):
            f.write('{} = {}\n'.format(name, var))
        f.write('Dumping error:\n')
        f.write('{}\n'.format(e))
        f.write('-' * 25 + '\n')

    # Write to stdout
    print('Exception raised in tweet_search')
    msg = []
    for name, var in zip('api, query, until_date, since_id, save_freq, local_filestore, num_iterations'.split(', '),
                        [api, query, until_date, since_id, save_freq, local_filestore, num_iterations]):
        msg.append('{}={}'.format(name, var))
    print('\n'.join(msg))
    print(e)

    # Send email
    send_email(subject='Exception raised in twitter_search.py',
               msg=('Exception raised in tweet_search function of twitter_search.py. '
                    '<br><br><b>Date</b> = {}'
                    '<br><br><b>Error:</b> <br>{}'
                    '<br><br><b>Vars:</b> <br>{}'.format(datetime.datetime.now(), e, '<br>'.join(msg))),
               destination_emails=['tagdata.ai@gmail.com'])

    # Break the loop if too many errors - to avoid infinite loops
    errors += 1
    if errors > max_errors:
        return 'break', errors

    return 'continue', errors


def tweet_search(api, term, query, found_ids, until_date='', since_id=0,
                 save_freq=1500, dw=None, local_filestore='', num_iterations=3,
                 testing_mode=False):
    """
    Search through recent tweets matching query, starting from previous ID
    if available or from oldest tweet exposed through the search API.
    """
    if not local_filestore:
        raise ValueError('Please specify local_filestore in tweet_search function')
    if not dw:
        # Connect to database
        dw = DataWriter(config['MONGO_DB_HOST'], config['MONGO_DB_PORT'])

    # Set date to start search (will search backwards from this point)
    if not until_date:
        until_date = (datetime.datetime.utcnow() - datetime.timedelta(days=1))\
                        .strftime('%Y-%m-%d')

    if testing_mode:
        save_freq = 5

    errors = 0
    max_errors = 5
    attempt = 0
    max_attempts = 1
    searched_tweets = []
    _since_id = since_id
    next_since_id = None
    _max_id = None
    # Run the tweet search loop. Starting at until_date and going back
    # until no more tweets are available OR the since_id is reached
    while True:
        try:
            # Twitter API searches backwards, starting at most recent
            # tweets above since_id and lower than max_id. We search
            # from max_id to since_id, updating max_id after each iteration.
            if _max_id:
                new_tweets = api.search(q=query, count=100,
                                        since_id=str(_since_id),
                                        max_id=str(_max_id),
                                        result_type='recent',
                                        until=until_date,
                                        tweet_mode='extended')
            else:
                new_tweets = api.search(q=query, count=100,
                                        since_id=str(_since_id),
                                        result_type='recent',
                                        until=until_date,
                                        tweet_mode='extended')
            time.sleep(3)

            for t in new_tweets:
                print(t._json['created_at'], t._json['id'])

            print('Found {} tweets'.format(len(new_tweets)))
            if not new_tweets:
                raise ValueError('No new tweets found')

            new_tweets_json = [t._json for t in new_tweets]
            print('len(new_tweets_json) before ID filter', len(new_tweets_json))

            # Save starting ID to define end point of next run
            if next_since_id == None:
                next_since_id = new_tweets_json[0]['id']

            # Update max ID to push back search threshold
            _max_id = int(new_tweets_json[-1]['id']) - 1
            print('max_id', _max_id)

            # Get IDs
            new_ids = set([t['id'] for t in new_tweets_json])

            # Filter out IDs already found 
            new_tweets_json = [t for t in new_tweets_json if t['id'] not in found_ids]
            print('len(new_tweets_json) after ID filter', len(new_tweets_json))

            # Update IDs
            found_ids = found_ids.union(new_ids)

            # Add metadata to tweets
            new_tweets_json = [{'term': term, 'q': query,
                                'get_date': datetime.datetime.utcnow().strftime(TWITTER_DATE_FORMAT),
                                'tweet': t} for t in new_tweets_json]

            # Extend list to be saved
            searched_tweets.extend(new_tweets_json)
            if len(searched_tweets) > save_freq:
                dw.write(searched_tweets, config['MONGO_DB_NAME'], config['MONGO_DB_COLLECTION'],
                            filename=os.path.join(local_filestore,
                                                term_to_filepath(term),
                                                '{}.json'.format(DATE_STR)))
                searched_tweets = []
                if testing_mode:
                    print('TEST MODE - Tweets saved, returning from tweet_search function')
                    return api, searched_tweets, found_ids, next_since_id

        except tweepy.TweepError:
            print('Rate limit reached, waiting 15 minutes')
            print('(until: {})'.format(datetime.datetime.now() + datetime.timedelta(minutes=15)))
            # t0 = time.time()
            dw.write(searched_tweets, config['MONGO_DB_NAME'], config['MONGO_DB_COLLECTION'],
                        filename=os.path.join(local_filestore,
                                            term_to_filepath(term),
                                            '{}.json'.format(DATE_STR)))
            searched_tweets = []
            # time.sleep((15 * 60) - (time.time() - t0))
            time.sleep(15 * 60)
            continue

        except ValueError as e:
            if 'No new tweets found' in str(e):
                attempt += 1
                if attempt > max_attempts:
                    print('No tweets found, stopping search')
                    break
                else:
                    print('No tweets found, trying {} more time(s)'\
                            .format(max_attempts - attempt + 1))
                    continue
                print('Re-loading the twitter API')
                api = load_api()
                print('Waiting for a few seconds ...')
                time.sleep(3)
            else:
                action, errors = log_errors(e, errors, max_errors,
                                            api, term, query, until_date, since_id,
                                            save_freq, local_filestore, num_iterations,
                                            testing_mode)
                if action == 'continue':
                    continue
                elif action == 'break':
                    break

        except Exception as e:
            action, errors = log_errors(e, errors, max_errors,
                                        api, term, query, until_date, since_id,
                                        save_freq, local_filestore, num_iterations,
                                        testing_mode)
            if action == 'continue':
                continue
            elif action == 'break':
                break

    dw.write(searched_tweets, config['MONGO_DB_NAME'], config['MONGO_DB_COLLECTION'],
                filename=os.path.join(local_filestore,
                                    term_to_filepath(term),
                                    '{}.json'.format(DATE_STR)))

    return api, searched_tweets, found_ids, next_since_id


def twitter_search(search_method,
         search_terms_file, search_terms_col,
         filter_method, num_iterations,
         testing_mode, flush_db):
    """
    Search from yesterday at midnight UTC time, up until the previous ID
    (in latest_tweet_id.txt) is reached. It iterated backwards and updates
    max_id to find new tweets.

    search_method : str
        Specify search method.
        $btc -> ticker
        #btc -> hashtag
        btc -> ''

    search_terms_file : str
        File containing terms to search for. In CSV format.
        Please pass search-term-col argument with column name.
        Note that your input search_terms_file path will be
        relative to the global data_path.

    search_terms_col : str
        Search terms column name in search_terms_file.

    filter_method : str
        Method to use for filtering tweets.
        For no filtering use none (''), other options are:
        - crypto

    num_iterations : int
        Iterate this many times over the full term list. The
        idea here is to find tweets that were missed due to
        incompleteness of twitter search API.

    testing_mode : bool
        Used when testing / developing. Scrapes less tweets.

    flush_db : bool
        Drop the mongodb database.
    """
    args = [config, search_method,
         search_terms_file, search_terms_col,
         filter_method, num_iterations,
         testing_mode, flush_db]
    arg_names = [i.strip() for i in """
                config, search_method,
                search_terms_file, search_terms_col,
                filter_method, num_iterations,
                testing_mode, flush_db
                """.split(',')]
    print_args(args, arg_names)

    start_time = time.time()

    if testing_mode:
        send_email('Hi there!',
                   'Running script in testing mode at {}'.format(datetime.datetime.now()),
                   ['tagdata.ai@gmail.com'])

    if flush_db:
        # Connect to database
        dw = DataWriter(config['MONGO_DB_HOST'], config['MONGO_DB_PORT'])
        dw.flush(config['MONGO_DB_NAME'])
        print('Database flushed. Stopping script.')
        return

    search_terms = read_search_terms(search_terms_file, search_terms_col)
    if testing_mode:
        # Limit the number of terms
        print('TEST MODE - Limiting the number of terms to 10.')
        search_terms = search_terms[:10]

    found_ids = {term: set() for term in search_terms}
                # TODO: *idea*
                # Avoid adding duplicate tweets.
                # Have collection of all tweets, and a lightweight collection
                # e.g. [{"term": "btc", "query": "$btc", "id": 2837127372}, ...etc]
    since_ids = {}
    for i_iter, _ in enumerate(range(num_iterations)):
        # Connect to database
        dw = DataWriter(config['MONGO_DB_HOST'], config['MONGO_DB_PORT'])
        len_0 = dw.get_collection_len(config['MONGO_DB_NAME'], config['MONGO_DB_COLLECTION'])

        for term in tqdm(search_terms):
            print('Term = {}'.format(term))

            # authorize and load the twitter API
            api = load_api()

            if search_method == 'ticker':
                q = '${}'.format(term)
            elif search_method == 'hashtag':
                q = '#{}'.format(term)
            else:
                q = term

            if filter_method:
                if filter_method == 'crypto':
                    trash_filters = ('-filter:retweets -filter:links '
                                    '-gainers -losers -alert -alerts -changes '
                                    '-change -changed -increased -decreased')
                else:
                    raise ValueError('Bad filter_method value: {}'.format(filter_method))
                q += ' {}'.format(trash_filters)

            print('Query = {}'.format(q))

            # Start searching for tweets from 1 day ago
            until_date = (DATE - datetime.timedelta(days=1)).strftime('%Y-%m-%d')

            # Search backwards until since_id is reached
            since_id = get_since_id(term)

            api, tweets, _found_ids, since_id = \
                tweet_search(api, term, q,
                             found_ids=found_ids[term],
                             since_id=since_id,
                             until_date=until_date,
                             local_filestore=os.path.join(config['DATA_PATH'], 'tweets'),
                             dw=dw,
                             testing_mode=testing_mode)

            found_ids[term] = _found_ids
            since_ids[term] = since_id

        print('Finished iteration = {}/{}'.format(i_iter + 1, num_iterations))

        # Get number of new tweets found, and write to file
        num_new_documents = dw.get_collection_len(config['MONGO_DB_NAME'], config['MONGO_DB_COLLECTION']) - len_0
        print('Saved {} new tweets'.format(num_new_documents))
        if not os.path.exists('num_iterations_report.log'):
            with open('num_iterations_report.log', 'w') as f:
                f.write('date,iteration,num_new_tweets_found\n')
        with open('num_iterations_report.log', 'a') as f:
            f.write('{},{},{},\n'.format(DATE_STR, i_iter, num_new_documents))

    dump_since_ids(since_ids)
    print('Done pulling data up to {} UTC'.format(DATE_STR))
    end_time = (time.time() - start_time) / 3600
    print('Runtime = {} hours'.format(end_time))
    with open(os.path.join(DIR_PATH, 'runtime.log'), 'a+') as f:
        f.write('{} - {} hours\n'.format(datetime.datetime.now(), end_time))


def print_args(args, arg_names):
    print('***** Arguments *****')
    max_space = max([len(name) for name in arg_names]) + 3
    for arg in zip(arg_names, args):
        print((arg[0] + ':').ljust(max_space), end='')
        print(arg[1])
    print('*'*21)


if __name__ == '__main__':
    args = load_config(var_type='args', script=SCRIPT_NAME)
    twitter_search(**args)


"""
tagdata.co                                                             
 _________   ________       _______        ________       ________     
/________/\ /_______/\     /______/\      /_______/\     /_______/\    
\__.::.__\/ \::: _  \ \    \::::__\/__    \::: _  \ \    \__.::._\/    
   \::\ \    \::(_)  \ \    \:\ /____/\    \::(_)  \ \      \::\ \     
    \::\ \    \:: __  \ \    \:\\_  _\/     \:: __  \ \     _\::\ \__  
     \::\ \    \:.\ \  \ \    \:\_\ \ \      \:.\ \  \ \   /__\::\__/\ 
      \__\/     \__\/\__\/     \_____\/       \__\/\__\/   \________\/ 
                                                                       
"""
