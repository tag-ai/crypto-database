# Run daily
cmd="python twitter_search.py --search-method=ticker --filter-method=crypto --search-terms-file=../../data/coin-master-list/coin-master-list.csv --search-terms-col=symbol"
echo $cmd
eval $cmd
