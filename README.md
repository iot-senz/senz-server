# How to install

### Python tools

sudo apt-get install build-essential  
sudo apt-get install python-dev  
sudo apt-get install python-twisted  
sudo apt-get install gcc-4.6 X  

### Setup Mongo DB

sudo apt-get install python-setuptools  
sudo apt-get install mongodb  
sudo apt-get install python-pip  
sudo pip install pymongo  
sudo service mongodb start  
mongo  
use mysensors  
db.users.insert({name:"kasun",skey:"11234",phone:"0773832923"})  

# Setup with docker

### Build docker images
docker build --tag senz/senzs .

### Run dockerize server
```
docker build --tag senz/switch .
docker run -it -p 9090:9090/udp -v /Users/eranga/sdbl/switch/logs:/app/senz/logs senz/switch
```

# Test server and client

### Start server

* Clone server   
* Start server python myServer.py  

### Start two clients
* Clone client into two places(senz-client1, senz-client2)
* Start client1 python myDevice.py (give username score)
* Start client2 python myDevice.py (give username wasn)

### Share senz
* From score: SHARE #lat #lon @wasn 
* From wasn: SHARE #lat #lon @score
