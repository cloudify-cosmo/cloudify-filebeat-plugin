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
#    * See the License for the specific language governing permissions and
#    * limitations under the License.


import os
import shutil
import unittest
import tempfile
import subprocess

import yaml
import distro
from mock import patch

from cloudify.mocks import MockCloudifyContext
from .. import tasks


distro_id = distro.id()
PATH = os.path.join(os.path.expanduser('~'), 'cloudify-filebeat-plugin')
TEMP_FILEBEAT = os.path.join(tempfile.gettempdir(), 'filebeat')
CONFIG_FILE = os.path.join(TEMP_FILEBEAT, 'filebeat.yml')
installation_file = os.path.join('/', 'etc', 'init.d', 'filebeat')


dict1_valid = {
    'inputs': {'shipper': None,
               'looging': {'rotateeverybytes': 10485760}},
    'outputs': {'logstash':
                {'hosts': ['http://localhost:5044'],
                 'bulk_max_size': 10,
                 'index': 'filebeat'},
                'elasticsearch':
                    {'hosts': ['http://localhost:9200'],
                     'path': 'filebeat.template.json'}},
    'paths': {'syslog': ['/var/log/syslog', '/var/log/auth.log'],
              'nginx-access': ['/var/log/nginx/*.log']}
}


def mock_read_file(resource_path):
    with open(resource_path) as f:
        return f.read()


def get_services():
    try:
        if distro_id in ('ubuntu', 'debian'):
            output = subprocess.check_output(['ps', '-A'])
        elif distro_id in ('centos', 'redhat'):
            output = subprocess.check_output(['rpm', '-qa'])
    except:
        "not installed"
    return output


class TestFilebeatPlugin(unittest.TestCase):

    def setUp(self):
        os.mkdir(TEMP_FILEBEAT)

    def tearDown(self):
        # Remove filebeat temp dir
        if os.path.exists(TEMP_FILEBEAT):
            shutil.rmtree(TEMP_FILEBEAT)
        if os.path.exists(os.path.join(tempfile.gettempdir(),
                                       'filebeat.yml')):
            os.remove(os.path.join(tempfile.gettempdir(), 'filebeat.yml'))

    @patch('filebeat_plugin.tasks.FILEBEAT_CONFIG_FILE_DEFAULT', CONFIG_FILE)
    @patch('filebeat_plugin.tasks.FILEBEAT_PATH_DEFAULT', TEMP_FILEBEAT)
    @patch('filebeat_plugin.tasks.ctx', MockCloudifyContext())
    def test_01_install_service(self):
        '''Verify service is available after installation -
         installation file is provided
         '''

        self.assertFalse(os.path.isfile(installation_file))

        if distro_id in ('ubuntu', 'debian'):
            tasks.install_filebeat('filebeat_1.2.3_amd64.deb', PATH)
        elif distro_id in ('centos', 'redhat'):
            tasks.install_filebeat('filebeat-1.2.3-x86_64.rpm', PATH)

        self.assertTrue(os.path.isfile(installation_file))

    @patch('filebeat_plugin.tasks.FILEBEAT_CONFIG_FILE_DEFAULT', CONFIG_FILE)
    @patch('filebeat_plugin.tasks.FILEBEAT_PATH_DEFAULT', TEMP_FILEBEAT)
    @patch('filebeat_plugin.tasks.ctx', MockCloudifyContext())
    def test_02_configure_with_inputs_no_file(self, *args):
        '''Validate configuration without file -
        rendered correctly and placed on the right place
        '''

        tasks.configure('', dict1_valid)
        self.assertTrue(os.path.exists(CONFIG_FILE))
        with open(CONFIG_FILE) as stream:
            try:
                yaml.load(stream)
            except yaml.YAMLError, exc:
                raise AssertionError(exc)
        output = subprocess.check_output(['filebeat',
                                          '-c',
                                          CONFIG_FILE,
                                          '-configtest'])
        self.assertNotIn('error', output)

    @patch('filebeat_plugin.tasks.FILEBEAT_CONFIG_FILE_DEFAULT', CONFIG_FILE)
    @patch('filebeat_plugin.tasks.FILEBEAT_PATH_DEFAULT', TEMP_FILEBEAT)
    @patch('filebeat_plugin.tasks.ctx', MockCloudifyContext())
    def test_03_failed_configure(self, *args):

        dict2_unvalid = {
            'inputs': None,
            'outputs': {'a': {'string': 'string'},
                        'b': None,
                        'c': {'list': ['a', 'b', 'c']}},
            'paths': {'a': {'string': 'string'},
                      'b': {'int': 10},
                      'c': {'list': None}}
        }
        self.assertRaises(ValueError, tasks.configure, '', dict2_unvalid)

        dict3_unvalid = {
            'inputs': {'a': None, 'b': {'int': 10},
                       'c': {'list': ['a', 'b', 'c']}},
            'outputs': None,
            'paths': {'a': {'string': 'string'}, 'b': None,
                      'c': {'list': ['a', 'b', 'c']}}
        }
        self.assertRaises(ValueError, tasks.configure, '', dict3_unvalid)

        dict4_unvalid = {
            'inputs': {'string': 'string', 'int': None,
                       'list': ['a', 'b', 'c']},
            'outputs': {'a': {'string': None},
                        'b': {'int': 10, 'list': ['a', 'b', 'c']}},
            'paths': '',
        }
        self.assertRaises(ValueError, tasks.configure, '', dict4_unvalid)

    @patch('filebeat_plugin.tasks.FILEBEAT_CONFIG_FILE_DEFAULT', CONFIG_FILE)
    @patch('filebeat_plugin.tasks.FILEBEAT_PATH_DEFAULT', TEMP_FILEBEAT)
    @patch('filebeat_plugin.tasks.ctx', MockCloudifyContext())
    @patch('cloudify.utils.get_manager_file_server_blueprints_root_url',
           return_value='')
    @patch('cloudify.manager.get_resource_from_manager',
           return_value=mock_read_file(os.path.join(
               'filebeat_plugin', 'tests', 'example_with_inputs.yml')))
    def test_04_configure_with_inputs_and_file(self, *args):
        '''Validate configuration with inputs and file
         rendered correctly and placed on the right place
         '''
        dict1_valid = {
            'inputs': {'shipper': None,
                       'looging': {'rotateeverybytes': 10485760}},
            'outputs': {'logstash':
                        {'hosts': ['http://localhost:5044'],
                         'bulk_max_size': 10,
                         'index': 'filebeat'},
                        'elasticsearch':
                            {'hosts': ['http://localhost:9200'],
                             'path': 'filebeat.template.json'}},
            'paths': {'syslog': ['/var/log/syslog', '/var/log/auth.log'],
                      'nginx-access': ['/var/log/nginx/*.log']}
        }

        tasks.configure(os.path.join('filebeat_plugin',
                                     'tests',
                                     'example_with_inputs.yml'), dict1_valid)
        self.assertTrue(os.path.exists(CONFIG_FILE))
        with open(CONFIG_FILE) as stream:
            try:
                yaml.load(stream)
            except yaml.YAMLError, exc:
                raise AssertionError(exc)

    @patch('filebeat_plugin.tasks.FILEBEAT_CONFIG_FILE_DEFAULT', CONFIG_FILE)
    @patch('filebeat_plugin.tasks.FILEBEAT_PATH_DEFAULT', TEMP_FILEBEAT)
    @patch('filebeat_plugin.tasks.ctx', MockCloudifyContext())
    @patch('cloudify.utils.get_manager_file_server_blueprints_root_url',
           return_value='')
    @patch('cloudify.manager.get_resource_from_manager',
           return_value=mock_read_file(
               os.path.join('filebeat_plugin', 'tests', 'example.yml')))
    def test_05_configure_with_file_without_inputs(self, *args):
        '''Validate configuration with file without inputs
         rendered correctly and placed on the right place
         '''

        tasks.configure(os.path.join(
            'filebeat_plugin', 'tests', 'example.yml'), None)
        self.assertTrue(os.path.exists(CONFIG_FILE))
        with open(CONFIG_FILE) as stream:
            try:
                yaml.load(stream)
            except yaml.YAMLError, exc:
                raise AssertionError(exc)

    @patch('filebeat_plugin.tasks.ctx', MockCloudifyContext())
    def test_06_start(self, *args):
        output = tasks.start()

        self.assertNotIn('error', output)

    @patch('filebeat_plugin.tasks.FILEBEAT_CONFIG_FILE_DEFAULT', CONFIG_FILE)
    @patch('filebeat_plugin.tasks.ctx', MockCloudifyContext())
    def test_07_start_failed_no_file(self, *args):
        self.assertRaises(ValueError, tasks.start)

    @patch('filebeat_plugin.tasks.ctx', MockCloudifyContext())
    def test_08_start_failed_with_file(self, *args):
        config = tempfile.NamedTemporaryFile(delete=False).name
        tasks._run('sudo mv {0} /etc/filebeat/filebeat.yml'.format(config))

        with self.assertRaises(SystemExit) as err:
            tasks.start()
        self.assertEqual(err.exception.code, 1)


class TestFilebeatInstall(unittest.TestCase):

    def setUp(self):
        os.mkdir(TEMP_FILEBEAT)

    @patch('filebeat_plugin.tasks.ctx', MockCloudifyContext())
    def tearDown(self):
        # Remove filebeat temp dir
        if os.path.exists(TEMP_FILEBEAT):
            shutil.rmtree(TEMP_FILEBEAT)
        if os.path.exists(os.path.join(tempfile.gettempdir(),
                                       'filebeat.yml')):
            os.remove(os.path.join(tempfile.gettempdir(), 'filebeat.yml'))
        tasks._run('sudo dpkg -r filebeat')
        try:
            tasks._run('sudo apt-get purge filebeat')
        except:
            pass

    @patch('filebeat_plugin.tasks.FILEBEAT_CONFIG_FILE_DEFAULT', CONFIG_FILE)
    @patch('filebeat_plugin.tasks.FILEBEAT_PATH_DEFAULT', TEMP_FILEBEAT)
    @patch('filebeat_plugin.tasks.ctx', MockCloudifyContext())
    @patch('cloudify.utils.get_manager_file_server_blueprints_root_url',
           return_value='')
    @patch('cloudify.manager.get_resource_from_manager',
           return_value=mock_read_file(
               os.path.join('filebeat_plugin', 'tests', 'example.yml')))
    def test_11_install_without_inputs(self, *args):
        """
        Verify Install function without inputs - only file
        """
        self.assertFalse(os.path.isfile(installation_file))

        tasks.install(filebeat_config_inputs=None,
                      filebeat_config_file=os.path.join(
                          'filebeat_plugin',
                          'tests',
                          'example.yml'))

        self.assertTrue(os.path.isfile(installation_file))

    @patch('filebeat_plugin.tasks.FILEBEAT_CONFIG_FILE_DEFAULT', CONFIG_FILE)
    @patch('filebeat_plugin.tasks.FILEBEAT_PATH_DEFAULT', TEMP_FILEBEAT)
    @patch('filebeat_plugin.tasks.ctx', MockCloudifyContext())
    def test_12_install_with_inputs(self, *args):
        """
        Verify Install function with inputs and default file
        """
        self.assertFalse(os.path.isfile(installation_file))

        tasks.install(filebeat_config_inputs=dict1_valid,
                      filebeat_config_file='')

        self.assertTrue(os.path.isfile(installation_file))

    @patch('filebeat_plugin.tasks.FILEBEAT_CONFIG_FILE_DEFAULT', CONFIG_FILE)
    @patch('filebeat_plugin.tasks.FILEBEAT_PATH_DEFAULT', TEMP_FILEBEAT)
    @patch('filebeat_plugin.tasks.ctx', MockCloudifyContext())
    @patch('cloudify.utils.get_manager_file_server_blueprints_root_url',
           return_value='')
    @patch('cloudify.manager.get_resource_from_manager',
           return_value=mock_read_file(os.path.join(
               'filebeat_plugin', 'tests', 'example_with_inputs.yml')))
    def test_13_install_with_file(self, *args):
        """
        Verify Install function with file and inputs
        """
        self.assertFalse(os.path.isfile(installation_file))

        tasks.install(filebeat_config_inputs=dict1_valid,
                      filebeat_config_file=os.path.join(
                          'filebeat_plugin',
                          'tests',
                          'example_with_inputs.yml'))

        self.assertTrue(os.path.isfile(installation_file))

    @patch('filebeat_plugin.tasks.FILEBEAT_CONFIG_FILE_DEFAULT', CONFIG_FILE)
    @patch('filebeat_plugin.tasks.FILEBEAT_PATH_DEFAULT', TEMP_FILEBEAT)
    @patch('filebeat_plugin.tasks.ctx', MockCloudifyContext())
    def test_14_install_path_exists(self, *args):
        """
        Verify Install function with path which already exists
        """

        path = tempfile.NamedTemporaryFile(delete=False)
        self.assertRaises(ValueError, tasks.install,
                          filebeat_config_inputs=dict1_valid,
                          filebeat_config_file='',
                          filebeat_install_path=path.name)
