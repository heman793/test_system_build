APP_NAME=IndexArb
echo "logfile /home/trader/apps/TradePlat/log/screenlog_%t_`date +%Y%m%d-%H%M%S`.log" >> /home/trader/apps/screenrc_temp
screen -L -t $APP_NAME -S $APP_NAME -d -m ./build64_release/IndexArb/$APP_NAME
