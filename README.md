# Crypto-twitter MongoDB Daily Update

*Only compatible with python 3*

## Overview
See blog post for more information: 

The twitter search API is used to pull tweets about a range of cryptocurrencies, e.g. $BTC or $ETH. The `twitter-search.py/twitter_search.py` script updates a mongodb database with the most recent tweets. Intended to be run daily.

![Crypto Twitter Project Graph](https://raw.githubusercontent.com/tag-ai/crypto-database/master/img/graphs/Crypto%20Twitter%20Data.png)

## Installation instructions   

```
# Install mongodb on mac
brew install mongodb

# Install mongodb on ubuntu (18.04)
sudo apt-get update
sudo apt-get upgrade
sudo apt install -y mongodb

# Create conda env
conda create --name crypto_twitter python=3.6

# Clone repo
git clone https://github.com/tag-ai/crypto-database.git
cd crypto-database

# Install libraries
source activate crypto_twitter
pip install -r scripts/twitter-search/requirements.txt
pip install -r scripts/utils/requirements.txt
```

## Configuring the project
```
vim scripts/twitter-search.py/cmd.sh

> # Run daily
> cmd="python twitter_search.py"
> echo $cmd
> eval $cmd

# Replace python with the absolute path
# to your anaconda python virtual env
# e.g. cmd="/home/alex/anaconda3/envs/crypto_twitter/bin/python twitter_search.py" 

# Make a folder for the database
# e.g.
mkdir -p data/CryptoData/mongodb_data

# Change database accordingly in start_mongodb_server.sh
```

## Running the scripts

```
# Start the mongo server
./start_mongodb_server.sh
# OR start manually (see below)
screen
mongod --dbpath=/path/to/database
# ctrl+d+a (to detach)

# Load the conda virtual env
conda activate crypto_twitter

# Run the script
cd /path/to/scripts/twitter-search && ./cmd.sh

# Exit the virtual env
source deactivate

# Close the mongo server
screen -r
# ctrl+d (to stop the mongo server)
exit
```

## Setting up cron jobs

```
crontab -e
# Paste the following lines
# (make sure to edit the path appropriately & leave at least one line of white space after)

0 10 * * * /path/to/repo/twitter-crypto-sentiments/master/scripts/twitter-search/cmd.sh > /path/to/repo/twitter-crypto-sentiments/master/scripts/twitter-search/cron.log 2>&1
```
