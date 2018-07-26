# Run mongo server on screen and detach
# will have to be closed manually later
# by running 'screen -r'
cmd="screen -d -m mongod --dbpath=/mnt/hdd-1/CryptoData"
echo $cmd
eval $cmd
