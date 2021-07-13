#
# Copyright 2021-22 Sharjah Islamic Bank
# authur: Muhammad Furqan <baqai.furqan@gmail.com>
# 
# imports:
# pip3 install schedule
# sudo apt install unixodbc-dev
# pip3 install pyodbc
# pip3 install dateparser


import os
import sys
import schedule
import time
import logging
import glob
import json
import shutil
import pyodbc
import dateutil.parser

#
# Command: export SI_SOURCE_LOG_DIR=/home/spire/source/sib/audit.logs && export SI_SI_POOL_INTERVAL=10 && SI_DEST_DIR=/home/spire/source/sib/audit.logs/archive && python3 BootStart.py
#  

# Logger Setup
# logging.basicConfig(level=logging.INFO,format='%(process)d-%(levelname)s-%(message)s')
logging.basicConfig(level=logging.INFO,format='%(asctime)s-%(levelname)s: %(message)s')
# %(asctime)s - %(name)s - %(levelname)s - %(message)s
# 

# Variables Definition
_ENV_SI_SI_POOL_INTERVAL     = 10 # Pool interval
_ENV_SI_SOURCE_LOG_DIR       = '' # os.path.dirname(os.path.realpath(__file__)) + '/audit.logs' # default location will come here
_ENV_SI_DEST_DIR             = '' # os.path.dirname(os.path.realpath(__file__)) + '/audit.logs/archive'
_ENV_SI_DB_SERVER            = ''
_ENV_SI_DB_DATABASE          = ''
_ENV_SI_DB_USERNAME          = ''
_ENV_SI_DB_PASS              = '' 
cursor = None
# END
_count = 0

# Shows banner on the screen
def showBanner():
    print("*****************************************");
    print("Bootstarting SiteInfinity logs parser");
    print("*****************************************");    
    print('Loading all log files from directory: '+_ENV_SI_SOURCE_LOG_DIR)
    print('Archive files directory: '+_ENV_SI_DEST_DIR)
    print('Pooling interval: '+ str(_ENV_SI_SI_POOL_INTERVAL) + ' seconds')
    pass    

# Load variables from environment variables
def loadEnvVariables():
    logging.info('Loading environment variables')
    global _ENV_SI_SOURCE_LOG_DIR,_ENV_SI_SI_POOL_INTERVAL,_ENV_SI_DEST_DIR  
    global _ENV_SI_DB_SERVER, _ENV_SI_DB_DATABASE, _ENV_SI_DB_USERNAME, _ENV_SI_DB_PASS
    _ENV_SI_SOURCE_LOG_DIR      = os.getenv('SI_SOURCE_LOG_DIR') if not os.getenv('SI_SOURCE_LOG_DIR') == None else os.path.dirname(os.path.realpath(__file__)) + '/audit.logs'
    _ENV_SI_SI_POOL_INTERVAL    = int(os.getenv('SI_POOL_INTERVAL')) if not os.getenv('SI_POOL_INTERVAL') == None else  10
    _ENV_SI_DEST_DIR            = os.getenv('SI_DEST_DIR') if not os.getenv('SI_DEST_DIR') == None else os.path.dirname(os.path.realpath(__file__)) + '/audit.logs/archive'
    _ENV_SI_DB_SERVER           = os.getenv('SI_DB_SERVER') 
    _ENV_SI_DB_DATABASE         = os.getenv('SI_DB_DATABASE') 
    _ENV_SI_DB_USERNAME         = os.getenv('SI_DB_USERNAME') 
    _ENV_SI_DB_PASS             = os.getenv('SI_DB_PASS')

    pass


# Starts Job scheduler as part of the 
def startScheduleJob():
    schedule.every(_ENV_SI_SI_POOL_INTERVAL).seconds.do(loadAndProcessFiles)
    while True:
        schedule.run_pending()
        time.sleep(1)    

# Load and process files
def loadAndProcessFiles():        
    logging.info('Loading files from the configured folder')
    ctrNoOfLines = 0    
    ctrNoOfFiles = 0
    allFiles = glob.glob(os.path.join(_ENV_SI_SOURCE_LOG_DIR, "*.log"))
    ctrNoOfFiles = len(allFiles)
    logging.info('Number of files detected: '+ str(ctrNoOfFiles))
    for file in allFiles:
        logging.info('Loading file: '+file)
        with open(file,"r") as f:
            contents     = f.readlines()
            ctrNoOfLines = len(contents)
            for content in contents:
                try:                    
                    parseContent(content) 
                except Exception as e:               
                    logging.error(f'Error while parsing content: {e!r}')
        # move file to archive location
        try:
            moveFile(file,_ENV_SI_DEST_DIR);
        except Exception as e:
            logging.error(f'Error while moving the file: {e!r}')
        # Show parse summary        
        logging.info('No of lines parsed: '+str(ctrNoOfLines))
    pass

def connectToMSSQL():
    # reference: https://cutt.ly/Mnj6p0l
    #            https://shorturl.at/hAFY9
    # Some other example server values are
    # server = 'localhost\sqlexpress' # for a named instance
    # server = 'myserver,port' # to specify an alternate port\
    # Installation of Driver:
    # Ref: https://github.com/Microsoft/mssql-docker/issues/448
    # Write below instruction in your docker file to make it work:
    # -======================================
    # RUN apt-get install curl
    # RUN apt-get install apt-transport-https
    # RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
    # RUN curl https://packages.microsoft.com/config/ubuntu/16.04/prod.list | tee /etc/apt/sources.list.d/msprod.list
    # 
    # RUN apt-get update
    # ENV ACCEPT_EULA=y DEBIAN_FRONTEND=noninteractive
    # RUN apt-get install mssql-tools unixodbc-dev -y    
    #
    drivers = [item for item in pyodbc.drivers()]
    if len(drivers) <= 0 :
        logging.error('Driver not found')
        raise Exception('Driver not found or not installed')
    driver = drivers[-1]
    
    server      = _ENV_SI_DB_SERVER
    database    = _ENV_SI_DB_DATABASE 
    username    = _ENV_SI_DB_USERNAME 
    password    = _ENV_SI_DB_PASS
    connStr     = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password};Connect Timeout=10;'
    logging.info(connStr)
    try:
        logging.info(f'Connectiong to database [{database}] on server [{server}] Using driver: [{driver}]')
        cnxn = pyodbc.connect(connStr)
        # cnxn = pyodbc.connect(f'Driver={driver};',
        #                         f'Server={server}',
        #                         f'Database={database}',
        #                         f'UID={username}',
        #                         f'PWD={password}',
        #                         f'Connection Timeout=10')
        logging.info(f'Connected SUCESFULLY')
    except Exception as e:
        logging.error(f'Error while connecting with the database: {e!r}')
    global cursor
    cursor = cnxn.cursor()
    pass

# Parse content
def parseContent(contentLine):
    # Skip line starting with '-'hyphen
    if contentLine.startswith('-'):
        return    
    jsonMainMessage     = json.loads(contentLine)
    # Loading specific variables from the root JSON message            
    loggedSeverity      = jsonMainMessage['LoggedSeverity']    
    timeStamp           = jsonMainMessage['TimeStamp']    
    machineName         = jsonMainMessage['MachineName']    
    processID           = str(jsonMainMessage['ProcessId'])    
    processName         = str(jsonMainMessage['ProcessName'])   
    # Parse JSON messages
    inlineMessage       = json.loads(jsonMainMessage['Message'])
    userName            = inlineMessage['UserName'] if 'UserName' in inlineMessage else ''    
    userID              = inlineMessage['UserID'] if not inlineMessage['UserID'] == None else ''        
    userIP              = inlineMessage['UserIP'] if 'UserIP' in inlineMessage else ''                                
    eventType           = inlineMessage['EventType'] if 'EventType' in inlineMessage else ''
    # Temp code for vieweing the json    
    global _count
    json_formatted_str = json.dumps(inlineMessage, indent=2)
    #print(json.dumps(json_formatted_str, indent=4, sort_keys=True))     
    # print('Writing content to the file')
    # with open(f'./archive/message_{_count}.json', 'w+') as f:
    #     f.write(json.dumps(inlineMessage))
    # _count = _count + 1
    # return               
    # END
    if eventType == '':
        eventType = 'UserLogin' if 'LoginResult' in inlineMessage else ''

    itemType            = inlineMessage['ItemType'] if 'ItemType' in inlineMessage else ''    
    itemFullType        = inlineMessage['ItemTypeFullName'] if 'ItemTypeFullName' in inlineMessage else ''    
    itemTitle           =  inlineMessage['ItemTitle'] if 'ItemTitle' in inlineMessage else ''    
    # Save the content in the database server    
    timeStamp           = dateutil.parser.parse(timeStamp)
    sqlInsert           = f"INSERT INTO [dbo].[audit_logs]([LoggedSeverity],[LogTime]," \
                              "[MachineName],[ProcessID],[ProcessName],[UserName],[UserID],[UserIP],[EventType]," \
                              "[ItemType],[ItemTypeFullName],[ItemTitle],[CreatedOn])" \
                              " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)"    
    
    global cursor
    ctrTrans            = cursor.execute(sqlInsert,loggedSeverity,timeStamp,machineName,
                               processID,processName,userName,userID,userIP,eventType,itemType,
                               itemFullType,itemTitle).rowcount    
    cursor.commit()
    logging.info(f'Data saved sucesfully. Records impacted: {ctrTrans}')

    pass

# Moves the file to archive location
def moveFile(file, destination):
    head, tail = os.path.split(file);
    logging.info('Moving file: '+ file+' to location: '+destination + '/'+ tail)
    shutil.move(file,os.path.join(destination + '/' + tail))    
    pass




if __name__ == '__main__':    
    loadEnvVariables(); # load argument variables
    showBanner()        # Display banner
    connectToMSSQL()    # Connect to the MSSQL server
    startScheduleJob()  # Start schedule job    