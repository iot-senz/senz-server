FROM ubuntu:latest

MAINTAINER Eranga Bandara (erangaeb@gmail.com)

# Update apt-get sources AND install required packages 
RUN apt-get update -y
RUN apt-get install -y apt-transport-https
RUN apt-get install -y build-essential
RUN apt-get install -y python-setuptools
RUN sudo apt-get -y install python-dev
RUN sudo apt-get install -y python-twisted

# Install pip and packages
RUN easy_install pip
RUN pip install pymongo

# Copy files 
ADD . /app/senz

# Volomue mapping for log directory
WORKDIR /app/senz
RUN rm -rf logs
RUN mkdir logs
VOLUME ["/app/senz/logs"]

# Service run on 9090 port
EXPOSE 9090 

# RUN server
CMD ["python", "/app/senz/myServer.py"]
