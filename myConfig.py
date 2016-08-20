import ConfigParser as cp

config = cp.RawConfigParser()
config.read('./config.cfg')

hostName=config.get("switch","switch-uri")
port=config.getint("switch","port")
serverName=config.get("switch","switch-name")

dbHost=config.get("database","db-host")
dbPort=config.getint("database","db-port")
dbName=config.get("database","db-name")
dbCollections=config.get("database","db-collections")

keyDir=config.get("keys","keys-dir")

if config.has_section("senz"):
    bootSenZ=config.get("senz","boot")

'''
print 'Switch-URL',hostName
print 'Port Number',port
print 'Switch Name',serverName

print 'DB host',dbHost
print 'DB port',dbPort
print 'DB-name',dbName
print 'DB-collections',dbCollections

'''
