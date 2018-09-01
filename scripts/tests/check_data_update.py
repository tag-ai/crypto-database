# -*- coding: utf-8 -*-
"""
check_data_update.py

Check if filestores & databases were updated.
Intended to be run daily.

Produces results (can be emailed):
    - Error report
    - Summary report

Author: Alex Galea
"""
import os
import json
import datetime
import numpy as np
import glob
import click
import sys
import textwrap
from pymongo import MongoClient
from tqdm import tqdm
sys.path.append('../utils')
from config import load_config
from emailer import send_email
SCRIPT_NAME = 'check_data_update'
DATE = datetime.datetime.utcnow()
DATE_STR = DATE.strftime('%Y-%m-%d')
config = load_config(var_type='globals', script=SCRIPT_NAME)

# Convert to absolute file paths
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
def absolute_path(path) -> str:
    return path if os.path.isabs(path) else os.path.join(DIR_PATH, path)
config['DATA_PATH'] = absolute_path(config['DATA_PATH'])
config['REPORT_FILE_PATH'] = absolute_path(config['REPORT_FILE_PATH'])
config['DB_INFO_FILE_PATH'] = absolute_path(config['DB_INFO_FILE_PATH'])


@click.command()
@click.option(
    '--raise-errors',
    is_flag=True,
    help='Override default behaviour of suppressing errors.'
)
def main(raise_errors):
    config['RAISE_ERRORS'] = raise_errors
    dc = DataContainer(config)
    summary_report(dc)
    dc.dump_db_info()
    dc.close()


def summary_report(dc):
    """
    Check if filestores & databases were updated.
    Intended to be run daily. Anything updates
    since last check will be quantified.
    """
    mc = MessageContainer()

    #-------------------------#
    # Check mongodb databases #
    #-------------------------#
    d = check_mongodbs(dc)
    o = '''
        Total rows
        Change in rows
        Total size (gb)
        Change in size (mb)
        '''
    mc.add('Mongodbs', d, o)

    #-------------------------#
    # Check local filestores  #
    #-------------------------#
    d = check_local_filestores(dc)
    o = '''
        Total CSV number
        Change in CSVs
        Newest CSV name
        Newest CSV lastmod
        '''
    mc.add('Local filestore', d, o)

    #-------------------------#
    # Check cron files        #
    #-------------------------#
    # d = check_cron_files(dc)
    # o = '''

    #     '''
    # mc.add('Cron files', d, o)

    mc.make_report(report_type='summary')


def check_mongodbs(dc) -> list((list, ...)):
    data = []
    mongo_dbs = {key: list([v for v in val.keys() if not v.startswith('_')])
                for key, val in dc.db_info['Mongodbs'].items()}
    for db, collections in mongo_dbs.items():
        for c in collections:
            id_str = '{} -> {}'.format(db, c)

            # Get total rows
            try:
                total_rows = dc.db_info['Mongodbs'][db][c]['count']
                total_rows = {id_str: '{0:+d}'.format(total_rows)}
            except Exception as e:
                if config['RAISE_ERRORS']:
                    raise e
                total_rows = {id_str: 'NaN rows (error finding value)'}

            # Get row diffs 
            row_diff = dc.get_delta('count',
                                      source='Mongodbs',
                                      layer_1=db, layer_2=c)
            if np.isnan(row_diff):
                row_diff = {id_str: 'NaN rows (error finding value)'}
            else:
                row_diff =  {id_str: '{0:+d}'.format(row_diff)}

            # Get row size
            try:
                total_size = dc.db_info['Mongodbs'][db][c]['storage_size']
                total_size =  {id_str: '{0:+.2f}'.format(total_size)}
            except Exception as e:
                if config['RAISE_ERRORS']:
                    raise e
                total_size = {id_str: 'NaN rows (error finding value)'}

            # Get size diffs 
            size_diff = dc.get_delta('storage_size',
                                source='Mongodbs',
                                layer_1=db, layer_2=c)
            if np.isnan(size_diff):
                size_diff = {id_str: 'NaN rows (error finding value)'}
            else:
                size_diff =  {id_str: '{0:+.2f}'.format(size_diff*1e3)}

        data.append([total_rows, row_diff, total_size, size_diff])

    return np.array(data).T.tolist()


def check_local_filestores(dc) -> list((list, ...)):
    data = []
    for group, folders in dc.db_info['Local filestore'].items():
        for folder in folders.keys():
            id_str = '{} -> {}'.format(group, folder)

            # Get total csv files
            try:
                total_csv_files = dc.db_info['Local filestore'][group][folder]['csv_file_count']
                total_csv_files = {id_str: '{0:+d}'.format(total_csv_files)}
            except Exception as e:
                if config['RAISE_ERRORS']:
                    raise e
                total_csv_files = {id_str: 'NaN rows (error finding value)'}

            # Get change in csv files
            csv_diff = dc.get_delta('csv_file_count',
                                      source='Local filestore',
                                      layer_1=group, layer_2=folder)
            if np.isnan(csv_diff):
                csv_diff = {id_str: 'NaN rows (error finding value)'}
            else:
                csv_diff = {id_str: '{1:+d}'.format(csv_diff)}

            # Get newest file name
            try:
                newest_file_name = dc.db_info['Local filestore'][group][folder]['newest_file']
                newest_file_name = {id_str: newest_file_name}
            except Exception as e:
                if config['RAISE_ERRORS']:
                    raise e
                newest_file_name = {id_str: 'NaN rows (error finding value)'}

            # Get newest file lastmod
            try:
                newest_file_lastmod = dc.db_info['Local filestore'][group][folder]['last_mod']
                newest_file_lastmod = {id_str: newest_file_lastmod}
            except Exception as e:
                if config['RAISE_ERRORS']:
                    raise e
                newest_file_lastmod = {id_str: 'NaN rows (error finding value)'}

        data.append([total_csv_files, csv_diff, newest_file_name, newest_file_lastmod])

    return np.array(data).T.tolist()


class MessageContainer:
    """
    Store summary/error messages
    to email and/or write to file.
    """
    def __init__(self):
        self.outputs = {}
        self.is_empty = True

    def add(self, desc, d, o):
        """
        Wrapper and data tansformer.
        """
        data = dict(zip((i.strip() for i in o.split('\n') if i.strip()), d))
        self._add(desc, data)

    def _add(self, desc: str, data: dict):
        """
        Add output.

        desc : str
            Category (function name)

        data : dict
            e.g. {
                "No new data": ["cryptocompare -> social"]
            }
        """
        if data:
            self.is_empty = False
            for k, v in data.items():
                if desc not in self.outputs.keys():
                    self.outputs[desc] = {}
                self.outputs[desc][k] = v

    def __str__(self):
        if self.is_empty:
            return 'No messages found'
        
        # return json.dumps(self.outputs, indent=4)

    def make_report(self, report_type,
                    to_screen=True, to_file=True, to_email=True):
        msg = textwrap.dedent('''\
            Date = {}
            Script = {}
            '''.format(DATE, SCRIPT_NAME))
        msg += '\n{}'.format(str(self))

        if to_screen:
            print(msg)

        if to_file:
            f_name = '{}_{}.txt'.format('-'.join(report_type.split()), DATE_STR)
            f_path = config['REPORT_FILE_PATH']
            if not os.path.exists(f_path):
                os.makedirs(f_path)
            f_path = os.path.join(f_path, f_name)
            with open(f_path, 'w') as f:
                f.write(msg)

        if to_email:
            msg_html = msg
            if not self.is_empty:
                if report_type == 'summary':
                    subject = 'Crypto Database: Daily Report'
                elif report_type == 'error':
                    subject = 'Cypto Databse: Flag Raised in Daily Update'
                else:
                    raise ValueError('Invalid report_type')
                send_email(subject, msg_html, config['REPORT_EMAILS'], content_type='text')
                print('Data sent to: {}'.format(config['REPORT_EMAILS']))
            else:
                print('No messages to send')


class DataContainer:
    """
    Manage mongodb client and
    store db_info/prev_db_info.
    """
    def __init__(self, config):
        self.config = config
        self.load_mongodb_client()
        self.load_db_info()
        self.load_prev_db_info()

    def load_mongodb_client(self):
        try:
            self.client = MongoClient(self.config['MONGO_DB_HOST'],
                                      self.config['MONGO_DB_PORT'])
            self.client_available = True
        except Exception as e:
            if config['RAISE_ERRORS']:
                raise e
            self.client = None
            self.client_available = False

    def close(self):
        self.client.close()

    def load_prev_db_info(self):
        f_path = config['DB_INFO_FILE_PATH'] 
        if not os.path.exists(f_path):
            os.makedirs(f_path)

        # Load prev. file
        try:
            f_name = sorted(glob.glob(os.path.join(f_path, '*.json')))[-1]
        except IndexError:
            self.prev_db_info = None
            return
        with open(f_name, 'r') as f:
            self.prev_db_info = json.load(f)

    def dump_db_info(self):
        # Overwrite prev file
        f_path = config['DB_INFO_FILE_PATH']
        if not os.path.exists(f_path):
            os.makedirs(f_path)
        f_name = '{}.json'.format('db_info')
        f_path = os.path.join(f_path, f_name)
        with open(f_path, 'w') as f:
            json.dump(self.db_info, f)

        # Save to archive
        f_path_archive = os.path.join(config['DB_INFO_FILE_PATH'], 'archive')
        if not os.path.exists(f_path_archive):
            os.makedirs(f_path_archive)
        f_name_archive = '{}_{}.json'.format('db_info', DATE_STR)
        f_path_archive = os.path.join(f_path_archive, f_name_archive)
        with open(f_path_archive, 'w') as f:
            json.dump(self.db_info, f)

    def load_db_info(self):
        self.db_info = {'Mongodbs': {},
                        'Local filestore': {}}

        dbs = [d for d in self.client.list_database_names()
                if d not in ('admin', 'config', 'local')]

        # Get mongodb stats
        for db_name in tqdm(dbs):
            db = self.client[db_name]
            self.add_db_stats(db, db_name=db_name)

        # Get local file stats
        for script_name, script_data_paths in self.config['DATA_PATHS'].items():
            self.add_local_fs_stats(script_data_paths, script_name)

    def add_db_stats(self, db, db_name):
        self.db_info['Mongodbs'][db_name] = {}
        branch = self.db_info['Mongodbs'][db_name]
        
        branch['_summary'] = {}
        d = db.command('dbstats')
        
        #-----------------------------------#
        # Mongodbs - Database storage size
        #-----------------------------------#
        try:
            storage_size = d['storageSize'] / 1e9
        except:
            storage_size = float('nan')
        branch['_summary']['storage_size'] = storage_size

        #-----------------------------------#
        # Mongodbs - Databse free space left
        #-----------------------------------#
        try:
            fs_free_space = (d['fsTotalSize'] - d['fsUsedSize']) / 1e9
        except:
            fs_free_space = float('nan')
        branch['_summary']['fs_free_space'] = fs_free_space

        for collection in db.list_collection_names():
            self.add_collection_stats(branch, db=db, collection_name=collection)
            
    def add_collection_stats(self, branch, db, collection_name):
        branch[collection_name] = {}
        d = db.command('collstats', collection_name)

        #----------------------------#
        # Mongodbs - Collection count
        #----------------------------#
        try:
            count = d['count']
        except:
            count = float('nan')
        branch[collection_name]['count'] = count

        #------------------------------------#
        # Mongodbs - Collection storage size
        #------------------------------------#
        try:
            storage_size = d['storageSize'] / 1e9
        except:
            storage_size = float('nan')
        branch[collection_name]['storage_size'] = storage_size

    def add_local_fs_stats(self, script_data_paths, script_name):
        self.db_info['Local filestore'][script_name] = {}
        branch = self.db_info['Local filestore'][script_name]
        
        # Check status of folders
        for rel_folder in script_data_paths['folders']:
            folder = os.path.join(self.config['DATA_PATH'], rel_folder)
            self.add_local_folder_stats(branch, folder, rel_folder)
        
        # Check status of files
        # TODO: implement this
    #     for file in script_data_paths['files']:
    #         add_local_file_stats(branch, file)
        
    def add_local_folder_stats(self, branch, folder, rel_folder):
        branch[rel_folder] = {}
        dir_files = glob.glob(os.path.join(folder, '*'))
        dir_csv_files = [d for d in dir_files if d.endswith('.csv')]
        
        #---------------------------------------------------#
        # Local filestore - Number of CSV files
        #---------------------------------------------------#
        try:
            csv_file_count = len(dir_csv_files)
        except:
            csv_file_count = float('nan')
        branch[rel_folder]['csv_file_count'] = csv_file_count
        
        #---------------------------------------------------#
        # Local filestore - Lastmod of most recent CSV file
        #---------------------------------------------------#
        try:
            newest_file, last_mod = sorted([(f, str(datetime.datetime.fromtimestamp(os.path.getmtime(f))))
                                            for f in dir_csv_files],
                                        key=lambda x: x[1])[-1]
            newest_file = os.path.split(newest_file)[-1]
        except:
            newest_file, last_mod = float('nan'), float('nan')
        branch[rel_folder]['newest_file'] = newest_file
        branch[rel_folder]['last_mod'] = last_mod

    def get_delta(self, what, source, layer_1, layer_2) -> int:
        try:
            current = self.db_info[source][layer_1][layer_2][what]
            prev = self.prev_db_info[source][layer_1][layer_2][what]
            out = current - prev
        except:
            out = float('nan')
        return out

if __name__ == '__main__':
    main()
