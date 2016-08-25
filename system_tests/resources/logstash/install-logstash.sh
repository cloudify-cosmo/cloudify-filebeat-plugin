#!/bin/bash

set -e


function install_logstash()
{
    ctx logger info  "installing logstash"
    sudo mkdir /opt/logstash
    cd /opt/logstash
    sudo wget https://download.elastic.co/logstash/logstash/packages/debian/logstash_2.3.3-1_all.deb
    sudo dpkg -i logstash_2.3.3-1_all.deb

    ctx logger info  "installing logstash contrib plugins"
    sudo /opt/logstash/bin/plugin install contrib

     ctx logger info  "Downloading conf file..."
    config_file_path=$(ctx download-resource-and-render logstash/logstash.conf)
	sudo mv ${config_file_path} /etc/logstash/conf.d/logstash.conf

    ctx logger info "logstash.conf was downloaded."


    # create logstash upstart file
#    echo 'description logstash' | sudo tee --append /etc/init/logstash.conf
#    echo 'start on runlevel [2345]' | sudo tee --append /etc/init/logstash.conf
#    echo 'stop on runlevel [016]' | sudo tee --append /etc/init/logstash.conf
#    echo 'kill timeout 60' | sudo tee --append /etc/init/logstash.conf
#    echo 'respawn' | sudo tee --append /etc/init/logstash.conf
#    echo 'respawn limit 10 5' | sudo tee --append /etc/init/logstash.conf
#    echo 'exec /opt/logstash/bin/logstash -f /opt/logstash/logstash.conf' | sudo tee --append /etc/init/logstash.conf
#    #ctx logger info  "Starting Logstash with conf file"
    #sudo start logstash
  
    # conf should include basic filtering and elasticsearch IP
    ctx logger info "installing logstash filebeats input"
    sudo /opt/logstash/bin/plugin install logstash-input-beats
    ctx logger info "starting logstash"
    sudo service logstash restart
}


function main(){
    ctx logger info  "preparing logstash environment..."
    sudo apt-get -y update &&
    ctx logger info  "installing dependencies"
#    sudo apt-get install -y vim openjdk-7-jdk &&
    install_logstash &&
    ctx logger info  "bootstrap done"
}

main

