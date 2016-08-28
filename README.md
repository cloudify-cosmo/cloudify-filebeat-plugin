++**WIP**++

cloudify-filebeat-plugin
========================

* Master Branch [![CircleCI](https://circleci.com/gh/cloudify-cosmo/cloudify-filebeat-plugin.svg?style=svg)](https://circleci.com/gh/cloudify-cosmo/cloudify-filebeat-plugin)

## Description

cloudify-filebeat-plugin is used to install & configure [filebeat](https://www.elastic.co/products/beats/filebeat) logs shipping platrofm on hosts.
Filebeats plaforms allows to collect logs from log files and systems and send them to desired destination (Elasticsearch and Logstash are recommended as output).
[Here you can see more inpormation regrading output options](https://www.elastic.co/guide/en/beats/filebeat/current/filebeat-configuration-details.html)

## Usage
cloudify-filebeat-plugin usage is very simple and require no more than config parameters as inputs. 
for each node which required filebeat platform - just enable the "monitoring agent" under the 'interface' section and provide the desired inputs. for example:

```yaml
  VM:
    type: cloudify.openstack.nodes.Server
    properties:
      resource_id: monitoring_ubuntu_server
      cloudify_agent:
    interfaces:
      cloudify.interfaces.monitoring_agent:
        install:
          implementation: filebeat.filebeat_plugin.tasks.install
          inputs:
            filebeats_install_path:
            download_url:
            filebeat_config_file:
            filebeat_config_inputs:
              paths:
                syslog:
                  - /var/log/syslog
                  - /var/log/auth.log
                nginx-access:
                  - /var/log/nginx/*.log
              outputs:
                logstash:
                  hosts:
                    - localhost:5044
                  bulk_max_size: 1024
                  index: filebeat
                elasticsearch:
                  hosts:
                    - localhost:9200
                  path: filebeat.template.json
              inputs:
                shipper:
                logging:
                  rotateeverybytes: 10485760
        start:
            implementation: filebeat.filebeat_plugin.tasks.start
```
As you can see, in order to add filebeat shipper to node - we provided 'filebeat_config_inputs' which is a dict with the following mandatory sub-dicts:
* **inputs**
* **outputs**
* **paths**

during the plugin installation process, a valid config file is generated - base on the inputs which provided.

Another option is to provide a ready and valid configuration file under 'filebeat_config_file' input (by default, this input is None).

> Notice! in order to provide valid inputs\config file, follow the [configuration editting instructions.](https://www.elastic.co/guide/en/beats/filebeat/current/filebeat-configuration.html)

Two additional inputs are:
* **filebeat_install_path** - sets the directory which thw system will be downloaded and install in (by default - set to be: /opt/filebeat)
* **download_url** - sets the url which filebeat will be downloaded from (by defaults - set to be from https://download.elastic.co/beats/filebeat, version 1.2.3)



