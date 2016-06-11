#!/bin/bash -e


IP=$(ctx target instance host_ip)
PROPERTY_NAME=$(ctx target node id)_ip
ctx logger info "Setting ${PROPERTY_NAME} Runtime Property."
ctx logger info "${PROPERTY_NAME} IP is: ${IP}"
ctx source instance runtime_properties ${PROPERTY_NAME} ${IP}
