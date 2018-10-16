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

## Dependencies & project config.
```
# Install Anaconda python 3+
# https://www.anaconda.com/download/
# Python 2 not supported

# Install mongodb on mac
brew install mongodb

# Install mongodb on ubuntu server (18.04)
sudo apt update
sudo apt upgrade
sudo apt install -y mongodb

# Install firefox on ubuntu server (18.04)
sudo apt-add-repository ppa:mozillateam/firefox-next
sudo apt update
sudo apt install firefox
# Go to the geckodriver releases page (https://github.com/mozilla/geckodriver/releases).
# Find the latest version of the driver for your platform and download it.
# e.g.
wget https://github.com/mozilla/geckodriver/releases/download/v0.21.0/geckodriver-v0.21.0-linux64.tar.gz
tar -xvzf geckodriver*
chmod +x geckodriver
sudo cp geckodriver /usr/bin/
sudo mv geckodriver /usr/local/bin/

# Create conda env
conda create --name crypto_database python=3.6

# Clone repo
git clone https://github.com/tagto/crypto-database.git
cd crypto-database

# Install the python libraries
source activate crypto_database
pip install -r scripts/twitter-search/requirements.txt
pip install -r scripts/rich-lists/requirements.txt
pip install -r scripts/cryptocompare/requirements.txt
pip install -r scripts/utils/requirements.txt

# Make a folder for the database
# e.g.
mkdir -p data/CryptoData/mongodb_data
# Open start_mongodb_server.sh and change dbpath to folder above ^

# Replace python with the absolute path
# to your anaconda python virtual env
# in "cmd*.sh" files of each script
# e.g. cmd="/home/alex/anaconda3/envs/crypto_database/bin/python twitter_search.py"
# in scripts/twitter-search. Do this for
# cmd*.sh files in other scripts folders also

# Add credentials for send email account
# and twitter search API
# (replace with your credentials)
vim scripts/utils/email_credentials.txt
vim twitter-account/api_token.json
```

## Setting up cron jobs

```
crontab -e
# Paste the following lines
# (make sure to edit the path appropriately & leave at least one line of white space after final command)

45 9 * * 0 /path/to/scripts/twitter-search/cmd_weekly_coin_list.sh > /path/to/scripts/twitter-search/cron.weekly_coin_list.log 2>&1
0 10 * * * /path/to/scripts/twitter-search/cmd_daily_twitter_search.sh > /path/to/scripts/twitter-search/cron.daily_twitter_search.log 2>&1

45 10 * * 0 /path/to/scripts/rich-lists/cmd_weekly_coin_map.sh > /path/to/scripts/rich-lists/cron.weekly_coin_map.log 2>&1
0 11 * * * /path/to/scripts/rich-lists/cmd_daily_cryptoid.sh > /path/to/scripts/rich-lists/cron.daily_cryptoid.log 2>&1
0 11 * * * /path/to/scripts/rich-lists/cmd_daily_etherscan.sh > /path/to/scripts/rich-lists/cron.daily_etherscan.log 2>&1

0 12 * * * /path/to/scripts/cryptocompare/cmd.sh > /path/to/scripts/cryptocompare/cron.log 2>&1
```

## Crypto Twitter

### Overview - MongoDB Daily Update
See blog post for more information: 

The twitter search API is used to pull tweets about a range of cryptocurrencies, e.g. $BTC or $ETH. The `twitter-search/twitter_search.py` script updates a mongodb database with the most recent tweets. Intended to be run daily.

![Crypto Twitter Project Graph](https://raw.githubusercontent.com/tag-ai/crypto-database/master/img/graphs/Crypto%20Twitter%20Data.png)

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
cd /path/to/scripts/twitter-search && ./cmd_weekly_coin_list.sh
cd /path/to/scripts/twitter-search && ./cmd_daily_twitter_search.sh

# Exit the virtual env
source deactivate

# Close the mongo server
screen -r
# ctrl+d (to stop the mongo server)
exit
```


## Rich Lists

### Overview - CSV Daily Download

See blog post for more information: 

A rich list is an array of the top addresses, for a given coin, and their holdings. This application uses various data sources to build a list of available coins and iterates over them, pulling the top X addresses & holding amounts. Scripts are intended to be run daily or weekly/monthy.

![Rich List Project Graph](https://raw.githubusercontent.com/tag-ai/crypto-database/master/img/graphs/Rich%20List%20Scrape.png)

### Running the scripts
```
# Load the conda virtual env
conda activate crypto_database

# If running headless mode, start browser
./start_headless_firefox_browser.sh
# OR start manually (see below)
screen
firefox --headless
# ctrl+d+a (to detach)

# Get the available coins for each data source
cd /path/to/scripts/rich-lists && ./cmd_weekly_coin_map.sh

# Get the rich lists
cd /path/to/scripts/rich-lists && ./cmd_daily_cryptoid.sh
cd /path/to/scripts/rich-lists && ./cmd_daily_etherscan.sh

# Exit the virtual env
source deactivate
```

## Cryptocopmare - Coin, Social Data

### Overview - MongoDB Daily Update
See blog post for more information: 

The cryptocompare API is used to pull social status & coin info for a range of cryptocurrencies, e.g. $BTC or $ETH. The `cryptocompare/cryptocompare_scrape.py` script updates a mongodb database with the most recent data. Intended to be run daily.

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
cd /path/to/scripts/cryptocompare && ./cmd.sh

# Exit the virtual env
source deactivate

# Close the mongo server
screen -r
# ctrl+d (to stop the mongo server)
exit
```

## License
[Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)](https://creativecommons.org/licenses/by-nc/4.0/)

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

