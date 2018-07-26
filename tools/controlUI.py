# -*- coding: utf-8 -*-
import paramiko 
import MySQLdb
import sys
from datetime import datetime
from time import sleep

todayStr = datetime.now().strftime('%Y-%m-%d')
username = 'trader'
passwd = 'admin@yansheng123'
serviceName = ''
ssh = None
cursor = None
FEMAS_ID1 = 100106759
FEMAS_ID2 = 100106760
DISABLE_FLAG = 0
ENABLE_FLAG = 1

def init(ipStr):
    global ssh 
    ssh = paramiko.SSHClient()  
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  
    ssh.connect(ipStr, 22, username, passwd)    
 
    try:
        conn = MySQLdb.connect(host=ipStr, user='admin', passwd='adminP@ssw0rd', db='common', charset='utf8')
    except Exception, e:
        print e 
        sys.exit(-1)
    global cursor     
    cursor = conn.cursor()   
    
def close():
    ssh.close()
    cursor.close()
       
def startIndexArb(chain):
    #启动IndexArb
    chain.send('cd ~/apps/IndexArb/\n')
    sleep(1)
    chain.send('bash start.indexarb.sh\n')                 
    sleep(3)  
    getStatus(chain, 'IndexArb') 
    print '>>Start IndexArb Over!'
    
def stopIndexArb(chain):
    chain.send('cd ~/apps/IndexArb/\n')    
    sleep(1)    
    chain.send('bash stop.indexarb.sh\n')       
    sleep(3) 
    getStatus(chain, 'IndexArb')    
    print '>>Stop IndexArb Over!'
         
def startCTA(chain):
    chain.send('cd ~/apps/CTA/\n')
    sleep(1)
    chain.send('bash start.cta.sh\n')                 
    sleep(3)  
    getStatus(chain, 'CTA') 
    print '>>Start CTA Over!'     

def stopCTA(chain):
    chain.send('cd ~/apps/CTA/\n')
    sleep(1)
    chain.send('bash stop.cta.sh\n')                 
    sleep(3)  
    getStatus(chain, 'CTA') 
    print '>>Stop CTA Over!'

def startPosition(chain):    
    chain.send('cd ~/dailyjob/DerivativesClient/\n')
    sleep(1)
    chain.send('./run.DerivativesClient_position.sh\n')                 
    sleep(90)  
    vaildatePosition()     
    print '>>Start Position Over!'  
    
def updateAccountStatus(accountID, flag):
    #禁用或启用femas账号
    sql = "update portfolio.real_account p set p.`ENABLE` = %s where p.AccountType = 'FEMAS' and p.accountName = %s"
    param = (flag, accountID)
    cursor.execute(sql, param)   
    
def coverConfigFile(femas_id):
    chain.send('cp /apps/CTA/config.cta.txt.%s /apps/CTA/config.cta.txt\n') % (femas_id,)
    sleep(1)
    
      
def vaildatePosition():    
    sql = "SELECT update_time,count(1) from (select DATE_FORMAT(UPDATE_DATE, '%y-%m-%d %H:%m') as update_time FROM portfolio.account_position where DATE = %s) t group by update_time"
    param = (todayStr,)
    cursor.execute(sql, param)  
    print '----------------------------------------'    
    print  'update_time    number'    
    for h in cursor.fetchall():
        print  h[0], '    ', h[1] 
    print '----------------------------------------'             
    
def getStatus(chain, programName): 
    chain.send('ps -ef|grep %s\n' % (programName,))
    sleep(5) 
    print 'server return information:'
    print '----------------------------------------'
    print chain.recv(9999)
    print '----------------------------------------' 
    

if __name__=='__main__': 
    print 'Service list--->'
    print '   1.192.168.1.120(huaobao)' 
    print '   2.192.168.1.195(guoxin)'  
    print '   3.192.168.1.197(zhongxin)'                   
    serviceNumber = raw_input('choose service:')
    
    global serviceName
    if serviceNumber == '1':
        serviceName = 'huabao'
        print 'start to connect huabao service,please wait...'
        init('192.168.1.120')         
    elif serviceNumber == '2':
        serviceName = 'guoxin'
        print 'start to connect guoxin service,please wait...'
        init('192.168.1.195') 
    elif serviceNumber == '3':
        serviceName = 'zhongxin'
        print 'start to connect zhongxin service,please wait...'
        init('192.168.1.197')              
        
    flag=True
    chain = ssh.invoke_shell()
    while flag: 
        print 'choose your commands:'        
        print '>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>'        
        print '   1.Start IndexArb' 
        print '   2.Stop IndexArb'           
        print '   3.Start CTA'  
        print '   4.Stop CTA'         
        print '   5.Start Run Position'  
        print '   0.Exit'         
        print '>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>'        
        command = raw_input('>>')
        if command == '1':
            print '>>try to start IndexArb'
            if (serviceName == 'huabao'):
                updateAccountStatus(FEMAS_ID1, DISABLE_FLAG)                             
                updateAccountStatus(FEMAS_ID2, DISABLE_FLAG)            
            startIndexArb(chain)           
        elif command == '2':
            print '>>try to stop IndexArb'
            stopIndexArb(chain)            
        elif command == '3':
            print 'choose account first:'
            print '     1.', FEMAS_ID1 
            print '     2.', FEMAS_ID2  
            chooseID = raw_input('>>')
            #根据所选用户更改数据库中账户状态和配置文件
            if (chooseID == '1'):
                updateAccountStatus(FEMAS_ID1, ENABLE_FLAG)                             
                updateAccountStatus(FEMAS_ID2, DISABLE_FLAG)
                coverConfigFile(FEMAS_ID1)
            elif (chooseID == '2'):      
                updateAccountStatus(FEMAS_ID1, DISABLE_FLAG)                             
                updateAccountStatus(FEMAS_ID2, ENABLE_FLAG)
                coverConfigFile(FEMAS_ID2)
            sleep(2)    
            print '>>try to start CTA'
            startCTA(chain) 
        elif command == '4':
            print '>>try to stop CTA'
            stopCTA(chain)         
        elif command == '5':
            print '>>try to run Position'
            startPosition(chain)  
            vaildatePosition()            
        else:
            close()                       