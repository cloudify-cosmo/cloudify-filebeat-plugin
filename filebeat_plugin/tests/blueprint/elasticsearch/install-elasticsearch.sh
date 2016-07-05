#!/bin/bash

set -e



function install_elasticsearch()
{
    cluster_name=$1

    ctx logger info  "installing elasticsearch"

    sudo mkdir -p /opt/elasticsearch
    cd /opt/elasticsearch
    sudo wget https://download.elastic.co/elasticsearch/elasticsearch/elasticsearch-2.3.3.deb
    sudo dpkg -i elasticsearch-2.3.3.deb


    # install plugins
    sudo /usr/share/elasticsearch/bin/plugin --install mobz/elasticsearch-head
    sudo /usr/share/elasticsearch/bin/plugin --install lmenezes/elasticsearch-kopf/1.2
    sudo /usr/share/elasticsearch/bin/plugin --install lukas-vlcek/bigdesk

    ctx logger info  "Downloading elasticsearch.yml file..."
    config_file_path=$(ctx download-resource-and-render elasticsearch/elasticsearch.yml)
	sudo mv ${config_file_path} /etc/elasticsearch/elasticsearch.yml
    ctx logger info "elasticsearch.yml was downloaded."

    ctx logger info  "starting elasticsearch server"
    sudo service elasticsearch restart
}


function main()
{
    ctx logger info  "preparing ES environment"
    sudo apt-get -y update &&
    ctx logger info  "installing dependencies"
    sudo apt-get install -y vim openjdk-7-jdk &&

    install_elasticsearch &&

    ctx logger info "Set the ElasticSearch IP runtime property"
    ELASTIC=$(ctx instance host_ip) 
    ctx logger info "ElasticSearch IP is ${ELASTIC} "    
    ctx instance runtime_properties elasticsearch_ip_address $(ctx instance host_ip)
    ctx logger info  "bootstrap done"
}

main

