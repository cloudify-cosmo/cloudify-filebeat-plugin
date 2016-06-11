#!/bin/bash -e
. $(ctx download-resource "utils")

ctx logger info "configuring hosts file..."
echo $(ctx instance runtime_properties vm_influxdb_master_ip)	vm-influxdb-master | sudo tee -a sudo /etc/hosts >/dev/null
echo $(ctx instance runtime_properties vm_influxdb_slave_ip)	vm-influx-slave | sudo tee -a sudo /etc/hosts >/dev/null
echo $(ctx instance runtime_properties vm_influxdb_kafka_slave_ip)	vm-kafka-extra | sudo tee -a sudo /etc/hosts >/dev/null

configure_component influxdb influxdb.conf /etc/influxdb/influxdb.conf

if [ $(ctx node id) = 'influxdb_slave' ] || [ $(ctx node id) = 'influxdb_extra' ]; then
	export INFLUXDB_IP=$(ctx instance runtime_properties vm_influxdb_master_ip)
	echo "INFLUXD_OPTS=\"-join ${INFLUXDB_IP}:8091\"" | sudo tee -a sudo /etc/default/influxdb > /dev/null
fi
