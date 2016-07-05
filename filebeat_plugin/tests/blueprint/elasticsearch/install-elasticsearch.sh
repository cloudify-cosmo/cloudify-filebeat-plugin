#!/bin/bash

set -e



function install_elasticsearch()
{
    cluster_name=$1

    ctx logger info  "installing elasticsearch"

    wget -qO - https://packages.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -
    echo "deb http://packages.elastic.co/elasticsearch/2.x/debian stable main" | sudo tee -a /etc/apt/sources.list.d/elasticsearch-2.x.list
    sudo apt-get -y update &&

    sudo apt-get -y install elasticsearch

#    sudo mkdir -p /opt/elasticsearch
#    cd /opt/elasticsearch
#    sudo wget https://download.elastic.co/elasticsearch/elasticsearch/elasticsearch-2.3.3.deb
#    sudo dpkg -i elasticsearch-2.3.3.deb


    ctx logger info  "starting elasticsearch server"
    sudo service elasticsearch restart
}


function main()
{


    ctx logger info  "preparing ES environment"
    sudo add-apt-repository -y ppa:webupd8team/java &&
    sudo apt-get -y update &&
    ctx logger info  "installing dependencies"
    sudo apt-get -y install oracle-java8-installer &&

    install_elasticsearch &&

    ctx logger info "Set the ElasticSearch IP runtime property"
    ELASTIC=$(ctx instance host_ip) 
    ctx logger info "ElasticSearch IP is ${ELASTIC} "    
    ctx instance runtime_properties elasticsearch_ip_address $(ctx instance host_ip)
    ctx logger info  "bootstrap done"
}

main


