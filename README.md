# Crypto Database Python Applications

<table>
  <body>
    <tr><td><a href="#crypto-twitter"><b>
      Crypto Twitter
    </b></a></td></tr>
    <tr><td><a href="#rich-lists"><b>
      Rich Lists
    </b></a></td></tr>
  </body>
</table>    

*Only compatible with python 3*

## Dependencies & installation
```
# Install mongodb on mac
brew install mongodb

# Install mongodb on ubuntu (18.04)
sudo apt-get update
sudo apt-get upgrade
sudo apt install -y mongodb

# Create conda env
conda create --name crypto_database python=3.6

# Clone repo
git clone https://github.com/tag-ai/crypto-database.git
cd crypto-database

pip install -r scripts/utils/requirements.txt
```

## Crypto Twitter

### Overview - MongoDB Daily Update
See blog post for more information: 

The twitter search API is used to pull tweets about a range of cryptocurrencies, e.g. $BTC or $ETH. The `twitter-search.py/twitter_search.py` script updates a mongodb database with the most recent tweets. Intended to be run daily.

![Crypto Twitter Project Graph](https://raw.githubusercontent.com/tag-ai/crypto-database/master/img/graphs/Crypto%20Twitter%20Data.png)

### Configuring the project
```
# Install libraries
source activate crypto_database
pip install -r scripts/twitter-search/requirements.txt

vim scripts/twitter-search.py/cmd.sh

> # Run daily
> cmd="python twitter_search.py"
> echo $cmd
> eval $cmd

# Replace python with the absolute path
# to your anaconda python virtual env
# e.g. cmd="/home/alex/anaconda3/envs/crypto_database/bin/python twitter_search.py" 

# Make a folder for the database
# e.g.
mkdir -p data/CryptoData/mongodb_data

# Change database accordingly in start_mongodb_server.sh
```

### Running the scripts

```
# Start the mongo server
./start_mongodb_server.sh
# OR start manually (see below)
screen
mongod --dbpath=/path/to/database
# ctrl+d+a (to detach)

# Load the conda virtual env
conda activate crypto_database

# Run the script
cd /path/to/scripts/twitter-search && ./cmd.sh

# Exit the virtual env
source deactivate

# Close the mongo server
screen -r
# ctrl+d (to stop the mongo server)
exit
```

### Setting up cron jobs

```
crontab -e
# Paste the following lines
# (make sure to edit the path appropriately & leave at least one line of white space after)

0 10 * * * /path/to/repo/twitter-crypto-sentiments/master/scripts/twitter-search/cmd.sh > /path/to/repo/twitter-crypto-sentiments/master/scripts/twitter-search/cron.log 2>&1
```

## Rich Lists

### Overview - MongoDB Daily Update

See blog post for more information: 

A rich list is an array of the top addresses, for a given coin, and their holdings. This application uses various data sources to build a list of available coins and iterates over them, pulling the top X addresses & holding amounts. Scripts are intended to be run daily or weekly/monthy.

![Rich List Project Graph](https://raw.githubusercontent.com/tag-ai/crypto-database/master/img/graphs/Rich%20List%20Scrape.png)

### Configuring the project
```
# Install libraries
source activate crypto_database
pip install -r scripts/rich-list/requirements.txt


EDIT BELOW
vim scripts/twitter-search.py/cmd.sh

> # Run daily
> cmd="python twitter_search.py"
> echo $cmd
> eval $cmd

# Replace python with the absolute path
# to your anaconda python virtual env
# e.g. cmd="/home/alex/anaconda3/envs/crypto_database/bin/python twitter_search.py" 

# Make a folder for the database
# e.g.
mkdir -p data/CryptoData/mongodb_data

# Change database accordingly in start_mongodb_server.sh
```

### Running the scripts

```
# Load the conda virtual env
conda activate crypto_database

# Get the available coins for each data source
cd /path/to/scripts/rich-list && ./cmd_weekly.sh

# Get the rich lists
cd /path/to/scripts/rich-list && ./cmd_daily_cryptoid.sh
cd /path/to/scripts/rich-list && ./cmd_daily_etherscan.sh

# Exit the virtual env
source deactivate
```

### Setting up cron jobs

```
crontab -e
# Paste the following lines
# (make sure to edit the path appropriately & leave at least one line of white space after)


```

