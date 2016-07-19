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
os.mkdir(TEMP_FILEBEAT)


def mock_install_ctx():
    return MockCloudifyContext()


class TestFilebeatPlugin(unittest.TestCase):

    @patch('filebeat_plugin.tasks.FILEBEAT_CONFIG_FILE_DEFAULT', CONFIG_FILE)
    @patch('filebeat_plugin.tasks.FILEBEAT_PATH_DEFAULT', TEMP_FILEBEAT)
    @patch('filebeat_plugin.tasks.ctx', mock_install_ctx())
    def test_configure_with_inputs_no_file(self):
        '''validate configuration without file -
        rendered correctly and placed on the right place'''
        dict1 = {
            'inputs': {'string': 'string', 'int': 10, 'list': ['a', 'b', 'c']},
            'outputs': {'string': 'string', 'int': 10,
                        'list': ['a', 'b', 'c']},
            'paths': {'string': 'string', 'int': 10, 'list': ['a', 'b', 'c']}
        }
        tasks.configure('', dict1)
        self.assertTrue(os.isfile(CONFIG_FILE))
        with open(CONFIG_FILE, "r") as stream:
            try:
                yaml.load(stream)
            except yaml.YAMLError, exc:
                raise AssertionError(exc)
        output = subprocess.check_output(['filebeat',
                                          '-c',
                                          CONFIG_FILE,
                                          '-configtest'])
        self.assertNotIn('error', output)

        dict2 = {
            'inputs': None,
            'outputs': {'string': 'string', 'int': None, 'list': ['a',
                                                                  'b',
                                                                  'c']},
            'paths': {'string': 'string', 'int': 10, 'list': None}
        }
        tasks.configure('', dict2)
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

        dict3 = {
            'inputs': {'string': None, 'int': 10, 'list': ['a', 'b', 'c']},
            'outputs': None,
            'paths': {'string': 'string', 'int': 10, 'list': None}
        }
        tasks.configure('', dict3)
        with open(CONFIG_FILE) as stream:
            try:
                yaml.load(stream)
            except yaml.YAMLError, exc:
                raise AssertionError(exc)
        self.assertNotIn('error', output)

        dict4 = {
            'inputs': {'string': 'string', 'int': None,
                       'list': ['a', 'b', 'c']},
            'outputs': {'string': None, 'int': 10, 'list': ['a', 'b', 'c']},
            'paths': '',
        }
        tasks.configure('', dict4)
        with open(CONFIG_FILE) as stream:
            try:
                yaml.load(stream)
            except yaml.YAMLError, exc:
                raise AssertionError(exc)
        self.assertNotIn('error', output)

    @patch('filebeat_plugin.tasks.FILEBEAT_CONFIG_FILE_DEFAULT', CONFIG_FILE)
    @patch('filebeat_plugin.tasks.FILEBEAT_PATH_DEFAULT', TEMP_FILEBEAT)
    @patch('filebeat_plugin.tasks.ctx', mock_install_ctx())
    def test_configure_with_inputs_and_file(self):
        '''validate configuration with inputs and file
         rendered correctly and placed on the right place'''
        dict1 = {
            'inputs': {'string': 'string', 'int': 10, 'list': ['a', 'b', 'c']},
            'outputs': {'string': 'string', 'int': 10,
                        'list': ['a', 'b', 'c']},
        }

        tasks.configure('filebeat_plugin.tests.example_with_inputs.yml', dict1)
        self.assertTrue(os.isfile(CONFIG_FILE))
        with open(CONFIG_FILE) as stream:
            try:
                yaml.load(stream)
            except yaml.YAMLError, exc:
                raise AssertionError(exc)

    @patch('filebeat_plugin.tasks.FILEBEAT_CONFIG_FILE_DEFAULT', CONFIG_FILE)
    @patch('filebeat_plugin.tasks.FILEBEAT_PATH_DEFAULT', TEMP_FILEBEAT)
    @patch('filebeat_plugin.tasks.ctx', mock_install_ctx())
    def test_configure_with_file_without_inputs(self):
        '''validate configuration with file without inputs
         rendered correctly and placed on the right place'''

        tasks.configure('filebeat_plugin.tests.example.yml', None)
        self.assertTrue(os.isfile(CONFIG_FILE))
        with open(CONFIG_FILE) as stream:
            try:
                yaml.load(stream)
            except yaml.YAMLError, exc:
                raise AssertionError(exc)

    @patch('filebeat_plugin.tasks.FILEBEAT_CONFIG_FILE_DEFAULT', CONFIG_FILE)
    @patch('filebeat_plugin.tasks.FILEBEAT_PATH_DEFAULT', TEMP_FILEBEAT)
    @patch('filebeat_plugin.tasks.ctx', mock_install_ctx())
    def test_download_filebeat(self):
        '''test download_filebeat function'''
        filename = tasks.download_filebeat('', TEMP_FILEBEAT)
        if distro in ('ubuntu', 'debian'):
            self.assertEqual(filename, 'filebeat_1.2.3_amd64.deb')
        elif distro in ('centos', 'redhat'):
            self.assertEqual(filename, 'filebeat-1.2.3-x86_64.rpm')
        self.assertTrue(os.path.exists(os.path.join(TEMP_FILEBEAT, filename)))

    @patch('filebeat_plugin.tasks.FILEBEAT_CONFIG_FILE_DEFAULT', CONFIG_FILE)
    @patch('filebeat_plugin.tasks.FILEBEAT_PATH_DEFAULT', TEMP_FILEBEAT)
    @patch('filebeat_plugin.tasks.ctx', mock_install_ctx())
    def test_download_file(self):
        '''test download -  verify file exists after download'''
        filename = tasks._download_file(
            'https://download.elastic.co/beats/filebeat/' +
            'filebeat_1.2.3_amd64.deb',
            PATH)
        self.assertEqual(filename, 'filebeat_1.2.3_amd64.deb')
        self.assertTrue(os.path.exists(filename))

    @patch('filebeat_plugin.tasks.FILEBEAT_CONFIG_FILE_DEFAULT', CONFIG_FILE)
    @patch('filebeat_plugin.tasks.FILEBEAT_PATH_DEFAULT', TEMP_FILEBEAT)
    @patch('filebeat_plugin.tasks.ctx', mock_install_ctx())
    def test_download_file_failed(self):
        '''test download - verify nothing downloaded'''
        filename = tasks._download_file(None, None)
        self.assertEqual(filename, None)
        # self.assertFalse(os.path.exists(filename))

    @patch('filebeat_plugin.tasks.FILEBEAT_CONFIG_FILE_DEFAULT', CONFIG_FILE)
    @patch('filebeat_plugin.tasks.FILEBEAT_PATH_DEFAULT', TEMP_FILEBEAT)
    @patch('filebeat_plugin.tasks.ctx', mock_install_ctx())
    def test_install_service(self):
        '''verify service is available after installation -
         installation file is provided'''
        if distro in ('ubuntu', 'debian'):
            tasks.install_filebeat('filebeat_1.2.3_amd64.deb', PATH)
            output = subprocess.check_output(['dpkg', '-l', 'filebeat'])
            self.assertIn('filebeat', output)
        elif distro in ('centos', 'redhat'):
            tasks.install_filebeat('filebeat-1.2.3-x86_64.rpm', PATH)
            output = subprocess.check_output(['rpm', '-qa'])
            self.assertIn('filebeat', output)
