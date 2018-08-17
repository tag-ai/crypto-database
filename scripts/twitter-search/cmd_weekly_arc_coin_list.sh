# Run daily
cd /home/alex/twitter-crypto-sentiments/master/scripts/update-twitter-search-coin-list
cmd="/home/alex/anaconda3/envs/crypto_database/bin/python update_twitter_search_coin_list.py --data-path=/mnt/hdd-1/CryptoData"
echo $cmd
eval $cmd
