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


distro = distro.id()
PATH = os.path.dirname(__file__)
TEMP_FILEBEAT = os.path.join(tempfile.gettempdir(), 'filebeat')
CONFIG_FILE = os.path.join(TEMP_FILEBEAT, 'filebeat.yml')


def mock_install_ctx():
    return MockCloudifyContext()


def mock_get_resource_from_manager(resource_path):
    with open(resource_path) as f:
        return f.read()


class TestFilebeatPlugin(unittest.TestCase):

    def tearDown(self):
        # remove filebeat temp dir
        if os.path.exists(TEMP_FILEBEAT):
            shutil.rmtree(TEMP_FILEBEAT)

    @patch('filebeat_plugin.tasks.FILEBEAT_CONFIG_FILE_DEFAULT', CONFIG_FILE)
    @patch('filebeat_plugin.tasks.FILEBEAT_PATH_DEFAULT', TEMP_FILEBEAT)
    @patch('filebeat_plugin.tasks.ctx', mock_install_ctx())
    def test_install_service(self):
        '''verify service is available after installation -
         installation file is provided'''
        os.mkdir(TEMP_FILEBEAT)

        if distro in ('ubuntu', 'debian'):
            tasks.install_filebeat('filebeat_1.2.3_amd64.deb', PATH)
            output = subprocess.check_output(['dpkg', '-l', 'filebeat'])
            self.assertIn('filebeat', output)
        elif distro in ('centos', 'redhat'):
            tasks.install_filebeat('filebeat-1.2.3-x86_64.rpm', PATH)
            output = subprocess.check_output(['rpm', '-qa'])
            self.assertIn('filebeat', output)

    @patch('filebeat_plugin.tasks.FILEBEAT_CONFIG_FILE_DEFAULT', CONFIG_FILE)
    @patch('filebeat_plugin.tasks.FILEBEAT_PATH_DEFAULT', TEMP_FILEBEAT)
    @patch('filebeat_plugin.tasks.ctx', mock_install_ctx())
    def test_configure_with_inputs_no_file(self, *args):
        '''validate configuration without file -
        rendered correctly and placed on the right place'''
        os.mkdir(TEMP_FILEBEAT)

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
    @patch('filebeat_plugin.tasks.ctx', mock_install_ctx())
    def test_failed_configure(self, *args):

        os.mkdir(TEMP_FILEBEAT)
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
        with open(CONFIG_FILE) as stream:
            try:
                yaml.load(stream)
            except yaml.YAMLError, exc:
                raise AssertionError(exc)

        dict3_unvalid = {
            'inputs': {'a': None, 'b': {'int': 10},
                       'c': {'list': ['a', 'b', 'c']}},
            'outputs': None,
            'paths': {'a': {'string': 'string'}, 'b': None,
                      'c': {'list': ['a', 'b', 'c']}}
        }
        self.assertRaises(ValueError, tasks.configure, '', dict3_unvalid)
        with open(CONFIG_FILE) as stream:
            try:
                yaml.load(stream)
            except yaml.YAMLError, exc:
                raise AssertionError(exc)

        dict4_unvalid = {
            'inputs': {'string': 'string', 'int': None,
                       'list': ['a', 'b', 'c']},
            'outputs': {'a': {'string': None},
                        'b': {'int': 10, 'list': ['a', 'b', 'c']}},
            'paths': '',
        }
        self.assertRaises(ValueError, tasks.configure, '', dict4_unvalid)
        with open(CONFIG_FILE) as stream:
            raise AssertionError(exc)

    @patch('filebeat_plugin.tasks.FILEBEAT_CONFIG_FILE_DEFAULT', CONFIG_FILE)
    @patch('filebeat_plugin.tasks.FILEBEAT_PATH_DEFAULT', TEMP_FILEBEAT)
    @patch('filebeat_plugin.tasks.ctx', mock_install_ctx())
    @patch('cloudify.utils.get_manager_file_server_blueprints_root_url',
           return_value='')
    @patch('cloudify.manager.get_resource_from_manager',
           return_value=mock_get_resource_from_manager(os.path.join(
               'filebeat_plugin', 'tests', 'example_with_inputs.yml')))
    def test_configure_with_inputs_and_file(self, *args):
        '''validate configuration with inputs and file
         rendered correctly and placed on the right place'''
        os.mkdir(TEMP_FILEBEAT)

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
    @patch('filebeat_plugin.tasks.ctx', mock_install_ctx())
    @patch('cloudify.utils.get_manager_file_server_blueprints_root_url',
           return_value='')
    @patch('cloudify.manager.get_resource_from_manager',
           return_value=mock_get_resource_from_manager(
               os.path.join('filebeat_plugin', 'tests', 'example.yml')))
    def test_configure_with_file_without_inputs(self, *args):
        '''validate configuration with file without inputs
         rendered correctly and placed on the right place'''
        os.mkdir(TEMP_FILEBEAT)

        tasks.configure(os.path.join(
            'filebeat_plugin', 'tests', 'example.yml'), None)
        self.assertTrue(os.path.exists(CONFIG_FILE))
        with open(CONFIG_FILE) as stream:
            try:
                yaml.load(stream)
            except yaml.YAMLError, exc:
                raise AssertionError(exc)
