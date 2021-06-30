# set base image (host OS)
FROM python:3.9.5

# set the working directory in the container
WORKDIR /opt/code

# copy the dependencies file to the working directory
# COPY BootStart.py .

# install dependencies
RUN apt-get install curl && \
    apt-get install apt-transport-https && \
    curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/ubuntu/16.04/prod.list | tee /etc/apt/sources.list.d/msprod.list && \
    apt-get update && \
    export ACCEPT_EULA=y && export DEBIAN_FRONTEND=noninteractive && \
    apt-get install mssql-tools unixodbc-dev -y && \
    apt-get install vim -y && \
    apt install unixodbc-dev && \
    sed -i 's/TLSv1.2/TLSv1.0/g' /etc/ssl/openssl.cnf && \
    sed -i 's/DEFAULT@SECLEVEL=2/DEFAULT@SECLEVEL=1/g' /etc/ssl/openssl.cnf && \
    pip3 install schedule && \
    pip3 install pyodbc && \
    pip3 install dateparser

# Setting environment variable
ENV SI_SOURCE_LOG_DIR=''
ENV SI_SI_POOL_INTERVAL=''
ENV SI_DEST_DIR=''
ENV SI_DB_SERVER=''
ENV SI_DB_DATABASE=''
ENV SI_DB_USERNAME=''
ENV SI_DB_PASS=''


# copy the content of the local src directory to the working directory
COPY . /opt/code

# command to run on container start
CMD [ "python", "./BootStart.py" ]