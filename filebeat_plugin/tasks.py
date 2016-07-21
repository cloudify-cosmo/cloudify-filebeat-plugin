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
import tempfile
import subprocess
import pkg_resources

import jinja2
import distro
import requests

from cloudify import ctx
from cloudify import exceptions
from cloudify.decorators import operation

import filebeat_plugin

distro = distro.id()
FILEBEAT_CONFIG_FILE_DEFAULT = os.path.join(
    '/', 'etc', 'filebeat', 'filebeat.yml')
FILEBEAT_PATH_DEFAULT = os.path.join('/', 'opt', 'filebeat')


@operation
def install(filebeat_config_inputs,
            filebeat_config_file='',
            filebeat_install_path='',
            download_url='',
            **kwargs):
    """Installation operation.

    Downloading and installing filebeat packacge - default version is 0.12.0.
    Default installation dir is set to /opt/filebeat.
    Only linux distributions are supported.
    """
    if 'linux' not in sys.platform:
        raise exceptions.NonRecoverableError(
            'Error! filebeat-plugin is available on linux distribution only')
    if not filebeat_install_path:
        filebeat_install_path = FILEBEAT_PATH_DEFAULT
    ctx.instance.runtime_properties[
        'filebeat_install_path'] = filebeat_install_path
    if os.path.isfile(filebeat_install_path):
        raise exceptions.NonRecoverableError(
            "Error! /opt/filebeat file already exists, can't create dir.")

    installation_file = download_filebeat(download_url, filebeat_install_path)
    install_filebeat(installation_file, filebeat_install_path)
    configure(filebeat_config_file, filebeat_config_inputs)


@operation
def start(**kwargs):
    """Start operation call for filebeat service,
    with filebeat_plugin configuration file.

    If filebeat service was already running -
    it will restart it and will use updated configuration file.
    """
    ctx.logger.info('Starting filebeat service...')
    filebeat_config_file = FILEBEAT_CONFIG_FILE_DEFAULT
    if not os.path.isfile(filebeat_config_file):
        raise exceptions.NonRecoverableError(
            "Can't start the service. Wrong config file provided")

    if os.path.exists('/usr/bin/systemctl'):
        _run('sudo systemctl restart filebeat')
    else:
        _run('sudo service filebeat restart')

    ctx.logger.info(
        'Good Luck! filebeat service is up!'
        'Have an awesome logging experience...')


def download_filebeat(download_url='', filebeat_install_path='', **kwargs):
    """Downloading filebeat package form your desire url.

    Default url set to be version 0.12.0
    anf downloaded from official influxdb site.
    """

    if not os.path.exists(filebeat_install_path):
        _run('sudo mkdir -p {0}'.format(filebeat_install_path))

    ctx.logger.info('Downloading filebeat...')

    if not download_url:
        if distro in ('ubuntu', 'debian'):
            download_url = 'https://download.elastic.co/beats/filebeat/' + \
                'filebeat_1.2.3_amd64.deb'
        elif distro in ('centos', 'redhat'):
            download_url = 'https://download.elastic.co/beats/filebeat/ ' + \
                'filebeat-1.2.3-x86_64.rpm'
        else:
            raise exceptions.NonRecoverableError(
                '''Error! distribution is not supported.
                Ubuntu, Debian, Centos and Redhat are supported currently''')
    installation_file = _download_file(download_url, filebeat_install_path)

    ctx.logger.info('filebeat downloaded.')
    return installation_file


def install_filebeat(installation_file, filebeat_install_path, **kwargs):
    """Depacking filebeat package."""
    ctx.logger.info('Installing filebeat...')

    if distro in ('ubuntu', 'debian'):
        install_cmd = 'sudo dpkg -i {0}'.format(
            os.path.join(filebeat_install_path, installation_file))
    elif distro in ('centos', 'redhat'):
        install_cmd = 'sudo rpm -vi {0}'.format(
            os.path.join(filebeat_install_path, installation_file))
    else:
        raise exceptions.NonRecoverableError(
            '''Error! distribution is not supported.
            Ubuntu, Debian, Centos and Redhat are supported currently''')
    _run(install_cmd)
    ctx.logger.info('filebeat service was installed...')


def configure(filebeat_config_file='', filebeat_config='', **kwargs):
    """Generating configuration file from your own desire destination
    or from filebeat_plugin filebeat.conf file.

    Rendering your inputs/outputs definitions.
    """
    ctx.logger.info('Configuring filebeat...')
    dest_file = os.path.join(tempfile.gettempdir(), 'filebeat.yml')
    if filebeat_config_file:
        try:
            ctx.download_resource_and_render(filebeat_config_file,
                                             dest_file,
                                             filebeat_config)
        except:
            print("wrong inputs prodided! can't redner configuration file")
            raise
    else:
        filebeat_config_file = pkg_resources.resource_string(
            filebeat_plugin.__name__, 'resources/filebeat.yml')
        configuration = jinja2.Template(filebeat_config_file)
        try:
            with open(dest_file, 'w') as f:
                f.write(configuration.render(filebeat_config))
        except:
            print("wrong inputs prodided! can't redner configuration file")
            raise
    _run('sudo mv {0} {1}'.format(dest_file, FILEBEAT_CONFIG_FILE_DEFAULT))
    ctx.logger.info('filebeat was configured...')


def _download_file(url, destination):
    try:
        filename = url.split('/')[-1]
    except:
        raise ValueError("wrong url provided! can't _download_file")
    temp_dir = tempfile.gettempdir()
    local_filename = os.path.join(temp_dir, filename)
    response = requests.get(url, stream=True)
    with open(local_filename, 'wb') as temp_file:
        for chunk in response.iter_content(chunk_size=512):
            if chunk:
                temp_file.write(chunk)
    _run('sudo mv {0} {1}'.format(local_filename, os.path.join(destination,
                                                               filename)))
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
