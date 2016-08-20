#!/usr/bin/env python
###############################################################################
##
##  My Sensor UDP Server v1.0
##  @Copyright 2014 MySensors Research Project
##  SCoRe Lab (www.scorelab.org)
##  University of Colombo School of Computing
##
##  Licensed under the Apache License, Version 2.0 (the "License");
##  you may not use this file except in compliance with the License.
##  You may obtain a copy of the License at
##
##      http://www.apache.org/licenses/LICENSE-2.0
##
##  Unless required by applicable law or agreed to in writing, software
##  distributed under the License is distributed on an "AS IS" BASIS,
##  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
##  See the License for the specific language governing permissions and
##  limitations under the License.
##
###############################################################################

from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
import sys
import os.path
import time
import logging

sys.path.append(os.path.abspath('./utils'))
sys.path.append(os.path.abspath('./senz'))
from senz import *
from myUser import *
from myCrypto import *
from myConfig import *


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# create a stdio handler
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)

# create a file handler
#handler = logging.FileHandler('logs/server.log')
#handler.setLevel(logging.INFO)

# create a logging format
formatter = logging.Formatter('[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s')

handler.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(handler)


# At present we manage connection in a dictionary.
# We save connection IP and port along with user/device name
connections = {}
connectionsTime = {}

#These global variables will be used to keep the server name and its public key
#serverName = "mysensors"
#UDP Server port number should be assigned here
#port = 9090

serverPubkey = ""
#Database connection will be kept in this variable
database = ""

# Here's a UDP version of the simplest possible SENZE protocol
class mySensorUDPServer(DatagramProtocol):
    '''
    # This method will create a new user at the
        server based on the following SENZE
    # SHARE #pubkey PEM_PUBKEY @mysensors #time timeOfRequest
        ^userName signatureOfTheSenze
    '''
    def createUser(self, senz, address):
        global database
        global serverName
        global serverPubkey

        usr = myUser(database,serverName)
        cry = myCrypto(serverName)
        data = senz.getData()
        pubkey = ''
        phone = ''
        reg_status = ''
        if 'pubkey' in data:
            pubkey = data['pubkey']
        if 'phone' in data:
            phone = data['phone']
        if cry.verifySENZE(senz, pubkey):
            reg_status = usr.addUser(senz.getSender(),phone, senz.getSENZE(),
                                 pubkey, senz.getSignature())

        logger.info('Registration status: %s' % reg_status)

        if reg_status == 'REGISTERED':
            st = 'DATA #msg REG_ALR #pubkey %s ' % (serverPubkey)
        elif reg_status == 'DONE':
            st = 'DATA #msg REG_DONE #pubkey %s ' % (serverPubkey)
        else:
            st = 'DATA #msg REG_FAIL #pubkey %s ' % (serverPubkey)
        senze = cry.signSENZE(st)
        self.transport.write(senze,address)
    '''
    # This methid will remove the user
         at the server based on the following SENZE
    # UNSHARE #pubkey @mysensors #time timeOfRequest
         ^userName signatureOfTheSenze
    '''
    def removeUser(self, sender, pubkey, address):
        global database
        global serverName

        usr = myUser(database, serverName)
        cry = myCrypto(serverName)
        status = usr.delUser(sender,pubkey)
        st = "DATA #msg "
        if status:
            st += 'UserRemoved'
        else:
            st += 'UserCannotRemoved'
        senze = cry.signSENZE(st)
        self.transport.write(senze, address)

    def shareSensors(self, senz):
        global connections
        global database
        global serverName
        """
        If query comes 'SHARE #tp @user2 #time t1 ^user1 siganture'
                                                     from the user1.
        First we need to verify that user2 is available.
        Then mysensors adds "user2" to the sensor dictionary at
                                                     user1's document and
        sensor name to the "user1" dictionary at user2's document.
        Finally it delivers the message SHARE #tp @user2 #time t1 ^user1
                                                     signature to user2.
        """
        sender = myUser(database, senz.getSender())

        recipients = senz.getRecipients()
        for recipient in recipients:
            if recipient in connections.keys():
                sender.share(recipient, senz.getSensors())

                logger.info('Sharing senz to: %s' % senz.getSender())
                logger.info('Sharing senz from: %s' % recipient)

                logger.info('______SHARED______')

                forward = connections[recipient]
                if forward != 0:
                    logger.info('Forward senz to: %s' % recipient)
                    self.transport.write(senz.getFULLSENZE(), forward)
                else:
                    logger.error('Not recipient found : %s' % recipient)

    def unshareSensors(self, senz):
        global connections
        global database
        usr = myUser(database, senz.getSender())
        recipients = senz.getRecipients()
        for recipient in recipients:
            if recipient in connections.keys():
                usr.unShare(recipient, senz.getSensors())
                forward = connections[recipient]
                if forward != 0:
                    self.transport.write(senz.getFULLSENZE(), forward)

    def GETSenze(self,senz):
        global connections
        global database
        global serverName

        sender = senz.getSender()
        sensors = senz.getSensors()
        usr = myUser(database, serverName)
        recipients = senz.getRecipients()
        for recipient in recipients:
            recipientDB = myUser(database, recipient)
            if 'pubkey' in sensors:
                #Since mysensors already has public key of it clients,
                #it responses on behalf of the client.
                pubkey = recipientDB.loadPublicKey()
                if pubkey != '':
                    if sender in connections.keys():
                        backward = connections[sender]
                        senze = 'DATA #name %s #pubkey %s' % (recipient,pubkey)
                        cry = myCrypto(serverName)
                        senze = cry.signSENZE(senze)
                        self.transport.write(senze, backward)
            #Otherwise GET message will forward to the recipients
            else:
                if recipient in connections.keys():
                    forward = connections[recipient]
                    if forward != 0 and \
                       recipientDB.isShare(sender, senz.getSensors()):
                        self.transport.write(senz.getFULLSENZE(), forward)
                    else:
                        logger.error('Senz not shared with recipient: %s' % recipient)
                else:
                    logger.error('No recipient found: %s' % recipient)

    def PUTSenze(self,senz):
        global connections
        global database

        sender = senz.getSender()
        usr = myUser(database, sender)
        recipients = senz.getRecipients()
        #PUT message will forward to the recipients
        for recipient in recipients:
            if recipient in connections.keys():
                recipientDB = myUser(database, recipient)
                if recipientDB.isShare(sender, senz.getSensors()):
                    forward = connections[recipient]
                    if forward != 0:
                        self.transport.write(senz.getFULLSENZE(), forward)
                    else:
                        logger.error('No recipient found: %s' % recipient)
                else:
                    logger.error('Senz not share with recipient: %s' % recipient)

    def DATASenze(self, senz):
        global connections
        global database

        sender = senz.getSender()
        usr = myUser(database, sender)
        recipients = senz.getRecipients()
        sensors = senz.getSensors()
        for recipient in recipients:
            if recipient in connections.keys():
                recipientDB = myUser(database, recipient)
                #DATA msg queries will always deliverd
                if recipientDB.isAllow(sender, sensors) or "msg" in sensors:
                    forward = connections[recipient]
                    if forward != 0:
                        self.transport.write(senz.getFULLSENZE(), forward)
                    else:
                        logger.error('No recipient found: %s' % recipient)
                else:
                    logger.error('Senz not shared with : %s' % recipient)

    # If Datagram Received, the following function will be called
    def datagramReceived(self, datagram, address):
        global serverName
        global database

        logger.info('senz received:  %s' % datagram)
        print datagram
        senz = SenZ(datagram)

        validQuery = False
        cry = myCrypto(serverName)
        senderDB = myUser(database,senz.sender)
        pubkey = senderDB.loadPublicKey()

        if senz.command == "SHARE" and "pubkey" in senz.sensors and serverName in senz.recipients:
            #Create a new account
            self.createUser(senz,address)
            validQuery = True

        elif senz.command == "UNSHARE" and "pubkey" in senz.sensors and\
                serverName in senz.recipients:
            #Remove the account
            if pubkey != "":
                if cry.verifySENZE(senz,pubkey):
                    status = self.removeUser(senz.sender, pubkey, address)
            validQuery = True

        else:
            if pubkey != "":
                if cry.verifySENZE(senz, pubkey):
                    validQuery = True

        if validQuery:
            connections[senz.sender] = address
            connectionsTime[senz.sender] = time.time()
            if senz.command == "SHARE":
                self.shareSensors(senz)
            elif senz.command == "UNSHARE":
                self.unshareSensors(senz)
            elif senz.command == "GET":
                self.GETSenze(senz)
            elif senz.command == "PUT":
                self.PUTSenze(senz)
            elif senz.command == "DATA":
                self.DATASenze(senz)

        else:
            senze = "DATA #msg SignatureVerificationFailed"
            senze = cry.signSENZE(senze)
            self.transport.write(senze, address)

    #Let's send a ping to keep open the port
    def sendPing(self, delay):
        global connections
        for recipient in connections:
            forward = connections[recipient]
            timeGap = time.time() - connectionsTime[recipient]
            #If there are no activities messages during in an hour * 24 (day),
            #let's close the connection
            if (timeGap < 3600 * 24):
                self.transport.write("PING", forward)
            else:
                connections[recipient] = 0
            #   connectionsTime.pop(recipient,None)
        reactor.callLater(delay, self.sendPing, delay=delay)

    #This function is called when we start the protocol
    def startProtocol(self):
        logger.info("Server started")
        self.sendPing(20)


def init():
# If servername is not there we will read the server name from keyboard
# else we will get it from config.cfg file
    global serverName
    global serverPubkey
    print "serverName",serverName
    try:
        if serverName == "":
            serverName = raw_input("Enter the server name:")
    except:
        logger.error("Cannot access server name")
        raise SystemExit

    # Here we will generate public and private keys for the server
    # These keys will be used to authentication
    # If keys are not available yet it will be generated
    global serverPubkey
    try:
        cry = myCrypto(serverName)
        if not os.path.isfile(cry.pubKeyLoc) and not os.path.isfile(cry.privKeyLoc):
            # Private key and public key was saved in the id_rsa and id_rsa.pub files
            cry.generateRSA(1024)
        serverPubkey = cry.loadRSAPubKey()
    except:
        logger.error("Cannot genereate private/public keys for the server.")
        raise SystemExit


def main():
    global database
    global port
    global dbHost,dbPort,dbName,dbCollections

    #Create connection to the Mongo DB
    try:
        logger.info("Accessing Mongo database.---")
        mongo_host = os.environ.get('MONGO_HOST',dbHost)
        client = MongoClient(mongo_host,dbPort)
        #Creating the database for the server
        db = client[dbName]
        # Access the user collection from the database
        database = db[dbCollections]
    except Exception:
        logger.info("Cannot access the Mongo database.")
        raise SystemExit

    reactor.listenUDP(port, mySensorUDPServer())
    reactor.run()

if __name__ == '__main__':
    init()
    logger.info(serverPubkey)
    main()
