########
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License fo########
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.
########
import os
import sys
import shlex
import subprocess
import pkg_resources

import jinja2
import distro
import requests

from cloudify import ctx
from cloudify import exceptions
from cloudify.decorators import operation

import logger_plugin


@operation
def install(filebeats_config_inputs, filebeats_config_file='',
            filebeats_install_path='', download_url='', **kwargs):
    """Installation operation.

    Downloading and installing filebeats packacge - default version is 0.12.0.
    Default installation dir is set to /opt/filebeats.
    Only linux distributions are supported.
    """
    if 'linux' not in sys.platform:
        raise exceptions.NonRecoverableError('''Error!
         filebeats-plugin is available on linux distribution only''')
    dist = distro.id()

    if not filebeats_install_path:
        filebeats_install_path = '/opt/filebeats'
    ctx.instance.runtime_properties[
        'filebeats_install_path'] = filebeats_install_path
    if os.path.isfile(filebeats_install_path):
        raise exceptions.NonRecoverableError(
            "Error! /opt/filebeats file already exists, can't create dir.")

    if not os.path.exists(filebeats_install_path):
        _run('sudo mkdir -p {0}'.format(filebeats_install_path))

    installation_file = download_filebeats(
        filebeats_install_path, dist, download_url)
    install_filebeats(filebeats_install_path, dist, installation_file)
    configure(filebeats_config_inputs, filebeats_config_file)


@operation
def start(filebeats_config_file='', **kwargs):
    """Start operation call for filebeats service,
    with filebeats_plugin configuration file.

    If filebeats service was already running -
    it will restart it and will use updated configuration file.
    """
    ctx.logger.info('Starting filebeats service...')
    if not filebeats_config_file:
        filebeats_config_file = '/etc/filebeat/filebeat.yml'
    if not os.path.isfile(filebeats_config_file):
        raise exceptions.NonRecoverableError("Config file doesn't exists")

    try:
        _run('sudo /etc/init.d/filebeat start')
    except SystemExit:
        _run('sudo service filebeats restart')

    ctx.logger.info(
        'GoodLuck! filebeats service is up!'
        'Have an awesome logging experience...')


def download_filebeats(filebeats_install_path, dist, download_url='', **kwargs):
    """Downloading filebeats package form your desire url.

    Default url set to be version 0.12.0
    anf downloaded from official influxdb site.
    """
    ctx.logger.info('Downloading filebeats...')

    if not download_url:
        if dist in ('ubuntu', 'debian'):
            download_url = 'https://download.elastic.co/beats/filebeat/filebeat_1.2.3_amd64.deb'
        elif dist in ('centos', 'redhat'):
            download_url = 'https://download.elastic.co/beats/filebeat/filebeat-1.2.3-x86_64.rpm'
        else:
            raise exceptions.NonRecoverableError(
                'Error! distribution is not supported')
    installation_file = _download_file(download_url, filebeats_install_path)

    ctx.logger.info('filebeats downloaded...installing..')
    return installation_file


def install_filebeats(filebeats_install_path, dist, installation_file, **kwargs):
    """Depacking filebeats package."""
    ctx.logger.info('Installing filebeats...')

    if dist in ('ubuntu', 'debian'):
        cmd = 'sudo dpkg -i {0}/{1}'.format(
            filebeats_install_path, installation_file)
    elif dist in ('centos', 'redhat'):
        cmd = 'sudo rpm -vi {0}/{1}'.format(
            filebeats_install_path, installation_file)
    else:
        raise exceptions.NonRecoverableError(
            'Error! distribution is not supported')
    _run(cmd)
    ctx.logger.info('filebeats service was installed...')


def configure(telgraf_config, filebeats_config_file='', **kwargs):
    """Generating configuration file from your own desire destination
    or from filebeats_plugin filebeats.conf file.

    Rendering your inputs/outputs definitions.
    """
    ctx.logger.info('Configuring filebeats.conf...')

    if not filebeats_config_file:
        filebeats_config_file_temp = pkg_resources.resource_string(
            filebeat_plugin.__name__, 'resources/filebeats.conf')
        configuration = jinja2.Template(filebeats_config_file_temp)
        filebeats_config_file = '/tmp/filebeats.conf'
        with open(filebeats_config_file, 'w') as f:
            f.write(configuration.render(telgraf_config))
    else:
        ctx.download_resource_and_render(filebeats_config_file,
                                         template_variables=telgraf_config)
    _run('sudo mv {0} /etc/filebeat/filebeat.yml'.format(filebeats_config_file))
    ctx.logger.info('filebeats.conf was configured...')


def _download_file(url, destination):
    filename = url.split('/')[-1]
    temp_dir = '/tmp'
    local_filename = os.path.join(temp_dir, filename)
    response = requests.get(url, stream=True)
    with open(local_filename, 'wb') as temp_file:
        for chunk in response.iter_content(chunk_size=512):
            if chunk:
                temp_file.write(chunk)
    _run('sudo mv {0} {1}'.format(local_filename, os.path.join(destination, filename)))
    return filename


def _run(command, retries=0, ignore_failures=False):
    if isinstance(command, str):
        command = shlex.split(command)
    stderr = subprocess.PIPE
    stdout = subprocess.PIPE

    ctx.logger.debug('Running: {0}'.format(command))
    proc = subprocess.Popen(command, stdout=stdout, stderr=stderr)
    proc.aggr_stdout, proc.aggr_stderr = proc.communicate()
    if proc.returncode != 0:
        command_str = ' '.join(command)
        if retries:
            ctx.logger.warn('Failed running command: {0}. Retrying. '
                            '({1} left)'.format(command_str, retries))
            proc = _run(command, retries - 1)
        elif not ignore_failures:
            ctx.logger.error('Failed running command: {0} ({1}).'.format(
                command_str, proc.aggr_stderr))
            sys.exit(1)
    return proc
