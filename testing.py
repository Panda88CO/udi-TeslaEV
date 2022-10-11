#!/usr/bin/env python3

#from TeslaCloudApi import teslaCloudApi
import sys
import time 
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
try:
    import udi_interface
    logging = udi_interface.LOGGER
    Custom = udi_interface.Custom
except ImportError:
    import logging
    logging.basicConfig(level=30)

token = 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IlR3bjV2bmNQUHhYNmprc2w5SUYyNnF4VVFfdyJ9.eyJpc3MiOiJodHRwczovL2F1dGgudGVzbGEuY29tL29hdXRoMi92MyIsImF1ZCI6Imh0dHBzOi8vYXV0aC50ZXNsYS5jb20vb2F1dGgyL3YzL3Rva2VuIiwiaWF0IjoxNjQ3OTk0Mzg4LCJzY3AiOlsib3BlbmlkIiwib2ZmbGluZV9hY2Nlc3MiXSwiZGF0YSI6eyJ2IjoiMSIsImF1ZCI6Imh0dHBzOi8vb3duZXItYXBpLnRlc2xhbW90b3JzLmNvbS8iLCJzdWIiOiJhNWY1Y2IyOS1hYjlkLTQ4ZGEtOTFlYS00YWIwY2Q1ZmJhZjYiLCJzY3AiOlsib3BlbmlkIiwiZW1haWwiLCJvZmZsaW5lX2FjY2VzcyJdLCJhenAiOiJvd25lcmFwaSIsImFtciI6WyJwd2QiXSwiYXV0aF90aW1lIjoxNjQ3OTk0Mzg3fX0.ZOgjCFQRSIImaul-PJ3n8P8NV6zBc718WE5Jsb_tx47qpCF0TEv3cEbO_-OyIwWSN1q8Limac3WaGx1mpA2UrYDTM5xFeECcM3-tdrNTNev6dysfdHZcsuK35txsa5t1NysbBWuZ-vckG2Eb5U3DS-otexS3ovdIueqay-eZVPZgqVNGRRpoSpHqqgHUcOrP7B_cGuaHR2ihTyvhlpZr4Rru6Jc9mf8x0e_RxfEMmuI0PVyTNYyZft3IDyKoObeLF5y5GpfjhJEPdsNjzzqWY-8kWGAcMFjnZlLFpB2L8TwLFvY0cWHEi_VAoH9h6qqeMpEqXlG1ZfN06f5CyRB-6A'
passwrd = '123COE!@#'



class test (object):
    def __init__ (self):

        if (os.path.exists('./saltToken.txt')):
            dataFile = open('./saltToken.txt', 'rb')
            self.SALT = dataFile.read()
            dataFile.close()
        else:
            self.SALT = os.urandom(16)
            print(type(self.SALT))
            
            dataFile = open('./saltToken.txt', 'wb')
            dataFile.write(self.SALT)
            dataFile.close()

    def readTokenFile(self, filename, password):
        logging.debug('Store Token File')
        passwd = password.encode()
        kdf = PBKDF2HMAC( algorithm=hashes.SHA256(), length=32, salt=self.SALT, iterations=390000 )
        key = base64.urlsafe_b64encode(kdf.derive(passwd))
        f = Fernet(key)
        if os.path.exists(filename):
            dataFile = open(filename, 'rb')
            tempStr = dataFile.read()
            dataFile.close()
            token = f.decrypt(tempStr)
            token=token.decode()
            return(token)
        else:
            return(False)

    def writeTokenFile(self, filename,  token, password):
        logging.debug('Retrieve Token File')
        passwd = password.encode()
        kdf = PBKDF2HMAC( algorithm=hashes.SHA256(), length=32, salt=self.SALT, iterations=390000, )
        key = base64.urlsafe_b64encode(kdf.derive(passwd))
        f = Fernet(key)
        Rtoken = f.encrypt(token.encode())
        dataFile = open(filename, 'wb')
        dataFile.write(Rtoken)
        dataFile.close()






tst = test()
#print(test)
#tst = teslaCloudApi()
tst.writeTokenFile('./testing.txt', token, passwrd)
temp = tst.readTokenFile('./testing.txt', passwrd)
print(temp)
print(type(temp))
print(token)
#temp = temp.decode()
print(type(token))
#print(type(temp))
print(temp == token)