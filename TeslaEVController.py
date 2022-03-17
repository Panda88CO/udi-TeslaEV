#!/usr/bin/env python3

#from os import truncate
import sys
import time 
import os
from TeslaEVInfo import tesla_info
from TeslaPWCtrlNodeNode import teslaPWSetupNode
from TeslaEVStatusNode import teslaEVStatusNode
#from TeslaEVChargeNode import teslaEVChargeNode
#from TeslaEVClimateNode import teslaPWGenNode
from TeslaCloudEVapi  import TeslaCloudAPI

try:
    import udi_interface
    logging = udi_interface.logging
    Custom = udi_interface.Custom
except ImportError:
    import logging
    logging.basicConfig(level=logging.DEBUG)






class TeslaEVController(udi_interface.Node):
    def __init__(self, polyglot, primary, address, name):
        super(TeslaEVController, self).__init__(polyglot, primary, address, name)
        self.poly = polyglot

        logging.info('_init_ Tesla Car Controller - 1')
        self.ISYforced = False
        self.name = 'Tesla Car Info'
        self.primary = primary
        self.address = address
        self.cloudAccess = False
        self.localAccess = False
        self.initialized = False

        self.poly.subscribe(self.poly.START, self.start, address)
        self.poly.subscribe(self.poly.LOGLEVEL, self.handleLevelChange)
        self.poly.subscribe(self.poly.CUSTOMPARAMS, self.handleParams)
        self.poly.subscribe(self.poly.POLL, self.systemPoll)
        self.poly.subscribe(self.poly.ADDNODEDONE, self.node_queue)
        self.n_queue = []


        self.Parameters = Custom(polyglot, 'customparams')
        self.Notices = Custom(polyglot, 'notices')
       
        logging.debug('self.address : ' + str(self.address))
        logging.debug('self.name :' + str(self.name))
        self.hb = 0
        #if not(PG_CLOUD_ONLY):
        
        self.nodeDefineDone = False
        self.longPollCountMissed = 0

        logging.debug('Controller init DONE')
        
        self.poly.ready()
        self.poly.addNode(self)
        self.wait_for_node_done()
        self.node = self.poly.getNode(self.address)
        self.node.setDriver('ST', 1, True, True)
        self.initialized = True
        logging.debug('finish Init ')



    def node_queue(self, data):
        self.n_queue.append(data['address'])

    def wait_for_node_done(self):
        while len(self.n_queue) == 0:
            time.sleep(0.1)
        self.n_queue.pop()


    def start(self):
       
        logging.debug('start')
        self.tesla_initialize()
        # Wait for things to initialize....
        while not self.initialized:
            time.sleep(1)

        # Poll for current values (and update drivers)
        self.TEV.pollSystemData('all')          
        self.updateISYdrivers('all')
        self.TEV.systemReady = True
   

    '''
    This may be called multiple times with different settings as the user
    could be enabling or disabling the various types of access.  So if the
    user changes something, we want to re-initialize.
    '''
    def tesla_initialize(self):
        logging.debug('starting Login process')
        try:
            #del self.Parameters['REFRESH_TOKEN']
            self.TEV = TeslaCloudAPI()
            vehicleList = self.TEV.teslaGetVehicleIdList()
            for vehicle in range(0,len(vehicleList)):
                vehicleInfo = self.TEV. teslaGetVehicleInfo(vehicleList[vehicle])
                vehicleName = vehicleInfo['respomse']['display_name']
                nodeAdr = 'vehicle'+str(vehicle+1)
                if not self.poly.getNode(nodeAdr):
                    node = teslaEVStatusNode(self.poly, self.address, nodeAdr, vehicleName,vehicleInfo, self.TEV)
                    self.poly.addNode(node)             
                    self.wait_for_node_done()
           
            '''           
           
            #self.TEV = tesla_info(self.name, self.address )
            if self.cloudAccess:
                logging.debug('Attempting to log in via cloud auth')
                self.TEV.loginCloud(cloud_email, cloud_password)
                self.cloudAcccessUp = self.TEV.teslaCloudConnect()
                #del self.Parameters['REFRESH_TOKEN']
                logging.debug('finished login procedures' )

            if not self.cloudAccess:
                logging.error('Configuration invalid, initialization aborted.')
                self.poly.Notices['err'] = 'Configuration is not valid, please update configuration.'
                return
            self.vehicles = {}
            EVlist = self.TEV.teslaGetVehicleIdList()
            logging.info('Creating Vehicle Nodes')
            for vehicle in range (0,len(EVlist)):
                id = EVlist[vehicle]
                EVinfo  = self.TEV.teslaGetVehicleInfo(id)
                nodeName = EVinfo['id_s']
                nodeAdr = 'vehicle'+str()
                if not self.poly.getNode(nodeAdr):
                    node = teslaEVStatusNode(self.poly, self.address, nodeAdr, nodeName, self.TEV)
                    self.poly.addNode(node)             
                    self.wait_for_node_done()
            
            '''
            self.nodeDefineDone = True
            self.initialized = True
            
        except Exception as e:
            logging.error('Exception Controller start: '+ str(e))
            logging.info('Did not connect to power wall')

        logging.debug ('Controller - initialization done')

    def handleLevelChange(self, level):
        logging.info('New log level: {}'.format(level))

    def handleParams (self, userParam ):
        logging.debug('handleParams')
        supportParams = ['CLOUD_USER_EMAIL', 'CLOUD_USER_PASSWORD', 'REFRESH_TOKEN'   ]
        self.Parameters.load(userParam)

        logging.debug('handleParams load')
        #logging.debug(self.Parameters)  ### TEMP
        self.poly.Notices.clear()
        cloud_valid = False
        self.cloudAccess = False
        for param in userParam:
            if param not in supportParams:
                del self.Parameters[param]
                logging.debug ('erasing key: ' + str(param))


        if 'CLOUD_USER_EMAIL' in userParam:
            cloud_email = userParam['CLOUD_USER_EMAIL']
        else:
            self.poly.Notices['cu'] = 'Missing Cloud User Email parameter'
            cloud_email = ''
            #self.Parameters['CLOUD_USER_EMAIL']  = cloud_email

        if 'CLOUD_USER_PASSWORD' in userParam:
            cloud_password = userParam['CLOUD_USER_PASSWORD']
        else:
            self.poly.Notices['cp'] = 'Missing Cloud User Password parameter'
            cloud_password = ''
            userParam['CLOUD_USER_PASSWORD']  = cloud_password

        if 'REFRESH_TOKEN' in userParam:
            cloud_token = userParam['REFRESH_TOKEN']
            if cloud_token != '':
                if (os.path.exists('./inputToken.txt')):
                    dataFile = open('./inputToken.txt', 'r')
                    tmpToken = dataFile.read()
                    dataFile.close()
                    if tmpToken != cloud_token:
                        dataFile = open('./inputToken.txt', 'w')
                        dataFile.write( cloud_token)
                        dataFile.close()
                        dataFile = open('./refreshToken.txt', 'w')
                        dataFile.write( cloud_token)
                        dataFile.close()   
                        self.Rtoken = cloud_token
                    elif (os.path.exists('./refreshToken.txt')): #assume refreshToken is newer
                        dataFile = open('./refreshToken.txt', 'r')
                        self.Rtoken = dataFile.read()
                        cloud_token = self.Rtoken
                        dataFile.close() 
                    else: #InputToken must exist (this should never trigger)
                        dataFile = open('./refreshToken.txt', 'w') 
                        dataFile.write( cloud_token)
                        dataFile.close()                   
                        self.Rtoken = cloud_token
                else: #first time input - must overwrite referehToken as well 
                    dataFile = open('./inputToken.txt', 'w')
                    dataFile.write( cloud_token)
                    dataFile.close()
                    dataFile = open('./refreshToken.txt', 'w')
                    dataFile.write( cloud_token)
                    dataFile.close()                        
                    self.Rtoken = cloud_token                    
            else: # nothing has changed - use refreshToken 
                if (os.path.exists('./refreshToken.txt')):
                    dataFile = open('./refreshToken.txt', 'r')
                    self.Rtoken = dataFile.read()
                    cloud_token = self.Rtoken
                    dataFile.close()
        else: #no token provided yet 
            if (os.path.exists('./refreshToken.txt')):
                dataFile = open('./refreshToken.txt', 'r')
                self.Rtoken = dataFile.read() 
                cloud_token = self.Rtoken  
                dataFile.close()
            else:
                self.poly.Notices['ct'] = 'Missing Cloud Refresh Token'
                cloud_token = ''

        cloud_valid = True
        if cloud_email == '' or cloud_password == '' or cloud_token == '':
            logging.debug('cloud access true, cfg = {} {} {}'.format(cloud_email, cloud_password, cloud_token))
            if cloud_email == '':
                self.poly.Notices['cu'] = 'Please enter the cloud user name'
                cloud_valid = False
            if cloud_password == '':
                self.poly.Notices['cp'] = 'Please enter the cloud user password'
                cloud_valid = False
            if cloud_token == '':
                self.poly.Notices['ct'] = 'Please enter the Tesla Refresh Token - see readme for futher info '
                cloud_valid = False


        if cloud_valid:
            logging.debug('Cloud access is valid, configure....')
            self.cloudAccess = True
            self.tesla_initialize( cloud_email, cloud_password)
        else:
            self.poly.Notices['cfg'] = 'Tesla PowerWall NS needs configuration.'

        logging.debug('done with parameter processing')
        
    def stop(self):
        #self.removeNoticesAll()
        if self.TEV:
            self.TEV.disconnectTEV()
        self.setDriver('ST', 0 )
        logging.debug('stop - Cleaning up')
        self.poly.stop()

    def heartbeat(self):
        logging.debug('heartbeat: ' + str(self.hb))
        
        if self.hb == 0:
            self.reportCmd('DON',2)
            self.hb = 1
        else:
            self.reportCmd('DOF',2)
            self.hb = 0
        
    def systemPoll(self, pollList):
        logging.debug('systemPoll')
        if self.TEV and self.nodeDefineDone and  self.TEV.systemReady:        
            if 'longPoll' in pollList:
                self.longPoll()
            elif 'shortPoll' in pollList:
                self.shortPoll()
        else:
            logging.info('Waiting for system/nodes to initialize')

    def shortPoll(self):
        logging.info('Tesla Power Wall Controller shortPoll')
        self.heartbeat()    
        if self.TEV.pollSystemData('critical'):
            for node in self.poly.nodes():
                node.updateISYdrivers('critical')
        else:
            logging.info('Problem polling data from Tesla system') 

        

    def longPoll(self):

        logging.info('Tesla Power Wall  Controller longPoll')

        if self.TEV.pollSystemData('all'):
            for node in self.poly.nodes():
                node.updateISYdrivers('all')
        else:
            logging.error ('Problem polling data from Tesla system')

    def updateISYdrivers(self, level):
        logging.debug('System updateISYdrivers - ' + str(level))       
        if level == 'all':
            value = self.TEV.isNodeServerUp()
            if value == 0:
               self.longPollCountMissed = self.longPollCountMissed + 1
            else:
               self.longPollCountMissed = 0
            self.setDriver('GV2', value)
            self.setDriver('GV3', self.longPollCountMissed)     
            logging.debug('CTRL Update ISY drivers : GV2  value:' + str(value) )
            logging.debug('CTRL Update ISY drivers : GV3  value:' + str(self.longPollCountMissed) )
        elif level == 'critical':
            value = self.TEV.isNodeServerUp()
            self.setDriver('GV2', value)   
            logging.debug('CTRL Update ISY drivers : GV2  value:' + str(value) )
        else:
            logging.error('Wrong parameter passed: ' + str(level))
 


    def ISYupdate (self, command):
        logging.debug('ISY-update called')
        if self.TEV.pollSystemData('all'):
            self.updateISYdrivers('all')
            #self.reportDrivers()
            for node in self.nodes:
                #logging.debug('Node : ' + node)
                if node != self.address :
                    self.nodes[node].longPoll()
 
    id = 'controller'
    commands = { 'UPDATE': ISYupdate }
    drivers = [
            {'driver': 'ST', 'value':0, 'uom':2},
            {'driver': 'GV2', 'value':0, 'uom':25},
            {'driver': 'GV3', 'value':0, 'uom':71}
            ]

if __name__ == "__main__":
    try:
        #logging.info('Starting Tesla Power Wall Controller')
        polyglot = udi_interface.Interface([])
        polyglot.start()
        polyglot.updateProfile()
        polyglot.setCustomParamsDoc()
        TeslaEVController(polyglot, 'controller', 'controller', 'Tesla EV node')
        polyglot.runForever()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
