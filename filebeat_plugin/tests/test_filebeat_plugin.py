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
import sys
import unittest
import tempfile
import subprocess

import yaml
import distro
from mock import patch


from cloudify.mocks import MockCloudifyContext
from .. import tasks
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))


distro = distro.id()
PATH = os.path.dirname(__file__)
TEST_SERVICE_NAME = 'filebeat'
TEST_RESOURCE_NAME = 'test_resource'
TEMP_FILEBEAT = os.path.join(tempfile.gettempdir(), 'filebeat')
CONFIG_FILE = os.path.join(TEMP_FILEBEAT, 'filebeat.yml')
os.mkdir(TEMP_FILEBEAT)


class MockNodeProperties(dict):

    def __init__(self, properties):
        self.update(properties)

    def get_all(self):
        return self


def mock_install_ctx():
    install_node_props = {'es_rpm_source_url': 'http://www.mock.com/fb.tar.gz',
                          'test_property': 'test'}
    return _create_mock_context(install_node_props)


def _create_mock_context(install_node_props,
                         node_id='fb_node',
                         service=TEST_SERVICE_NAME):
    return MockCloudifyContext(node_id=node_id,
                               node_name=service,
                               properties=install_node_props)


class TestFilebeatPlugin(unittest.TestCase):

    @patch('../tasks.FILEBEAT_CONFIG_FILE_DEFAULT', CONFIG_FILE)
    @patch('../tasks.FILEBEAT_INSTALL_PATH_DEFAULT', TEMP_FILEBEAT)
    @patch('../tasks.ctx', mock_install_ctx())
    def test_configure_with_inputs_no_file(self):
        '''validate configuration was rendered correctly
        and placed on the right place - with file comprison'''
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

        dict3 = {
            'inputs': {'string': None, 'int': 10, 'list': ['a', 'b', 'c']},
            'outputs': None,
            'paths': {'string': 'string', 'int': 10, 'list': None}
        }
        tasks.configure('', dict3)
        with open(CONFIG_FILE, "r") as stream:
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
        with open(CONFIG_FILE, "r") as stream:
            try:
                yaml.load(stream)
            except yaml.YAMLError, exc:
                raise AssertionError(exc)
        self.assertNotIn('error', output)

    @patch('../tasks.FILEBEAT_CONFIG_FILE_DEFAULT', CONFIG_FILE)
    @patch('../tasks.FILEBEAT_INSTALL_PATH_DEFAULT', TEMP_FILEBEAT)
    @patch('../tasks.ctx', mock_install_ctx())
    def test_configure_with_inputs_and_file(self):
        '''validate configuration was rendered correctly and
         placed on the right place - with file comprison'''
        dict1 = {
            'inputs': {'string': 'string', 'int': 10, 'list': ['a', 'b', 'c']},
            'outputs': {'string': 'string', 'int': 10,
                        'list': ['a', 'b', 'c']},
        }

        tasks.configure('example_with_inputs.yml', dict1)
        self.assertTrue(os.isfile(CONFIG_FILE))
        with open(CONFIG_FILE, "r") as stream:
            try:
                yaml.load(stream)
            except yaml.YAMLError, exc:
                raise AssertionError(exc)

    @patch('../tasks.FILEBEAT_CONFIG_FILE_DEFAULT', CONFIG_FILE)
    @patch('../tasks.FILEBEAT_INSTALL_PATH_DEFAULT', TEMP_FILEBEAT)
    @patch('../tasks.ctx', mock_install_ctx())
    def test_configure_with_file_without_inputs(self):
        '''validate configuration was rendered correctly and
         placed on the right place - with file comprison'''
        tasks.configure('example.yml', '')
        self.assertTrue(os.isfile(CONFIG_FILE))
        with open(CONFIG_FILE, "r") as stream:
            try:
                yaml.load(stream)
            except yaml.YAMLError, exc:
                raise AssertionError(exc)

    @patch('../tasks.FILEBEAT_CONFIG_FILE_DEFAULT', CONFIG_FILE)
    @patch('../tasks.FILEBEAT_INSTALL_PATH_DEFAULT', TEMP_FILEBEAT)
    @patch('../tasks.ctx', mock_install_ctx())
    def test_download_filebeat(self):
        '''verify file exists after download'''
        filename = tasks.download_filebeat('', PATH)
        if distro in ('ubuntu', 'debian'):
            self.assertEqual(filename, 'filebeat_1.2.3_amd64.deb')
        elif distro in ('centos', 'redhat'):
            self.assertEqual(filename, 'filebeat-1.2.3-x86_64.rpm')
        self.assertTrue(os.isfile(os.path.join(PATH, filename)))

    @patch('../tasks.FILEBEAT_CONFIG_FILE_DEFAULT', CONFIG_FILE)
    @patch('../tasks.FILEBEAT_INSTALL_PATH_DEFAULT', TEMP_FILEBEAT)
    @patch('../tasks.ctx', mock_install_ctx())
    def test_download_file(self):
        '''verify file exists after download'''
        filename = tasks._download_file(
            'https://download.elastic.co/beats/filebeat/' +
            'filebeat_1.2.3_amd64.deb',
            PATH)
        self.assertEqual(filename, 'filebeat_1.2.3_amd64.deb')
        self.assertTrue(os.isfile(filename))

    @patch('../tasks.FILEBEAT_CONFIG_FILE_DEFAULT', CONFIG_FILE)
    @patch('../tasks.FILEBEAT_INSTALL_PATH_DEFAULT', TEMP_FILEBEAT)
    @patch('../tasks.ctx', mock_install_ctx())
    def test_download_file_failed(self):
        '''verify nothing downloaded'''
        filename = tasks._download_file(None, None)
        self.assertEqual(filename, None)
        self.assertFalse(os.isfile(filename))

    @patch('../tasks.FILEBEAT_CONFIG_FILE_DEFAULT', CONFIG_FILE)
    @patch('../tasks.FILEBEAT_INSTALL_PATH_DEFAULT', TEMP_FILEBEAT)
    @patch('../tasks.ctx', mock_install_ctx())
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
