APP_NAME=MainFrame
echo "logfile /home/trader/apps/TradePlat/log/screenlog_%t_`date +%Y%m%d-%H%M%S`.log" > /home/trader/.screenrc
screen -L -t $APP_NAME -S $APP_NAME -d -m ./build64_release/$APP_NAME/$APP_NAME
