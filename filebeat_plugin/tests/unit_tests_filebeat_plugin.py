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
            try:
                shutil.rmtree(TEMP_FILEBEAT)
            except:
                subprocess.call(['sudo', 'rm', '-rf', TEMP_FILEBEAT])

    @patch('filebeat_plugin.tasks.FILEBEAT_CONFIG_FILE_DEFAULT', CONFIG_FILE)
    @patch('filebeat_plugin.tasks.FILEBEAT_PATH_DEFAULT', TEMP_FILEBEAT)
    @patch('filebeat_plugin.tasks.ctx', mock_install_ctx())
    def test_download_filebeat(self):
        '''test download_filebeat function'''
        os.mkdir(TEMP_FILEBEAT)

        filename = tasks.download_filebeat('', TEMP_FILEBEAT)
        if distro in ('ubuntu', 'debian'):
            self.assertEqual(filename, 'filebeat_1.2.3_amd64.deb')
        elif distro in ('centos', 'redhat'):
            self.assertEqual(filename, 'filebeat-1.2.3-x86_64.rpm')
        self.assertTrue(os.path.exists(os.path.join(TEMP_FILEBEAT, filename)))

    @patch('filebeat_plugin.tasks.FILEBEAT_CONFIG_FILE_DEFAULT', CONFIG_FILE)
    @patch('filebeat_plugin.tasks.FILEBEAT_PATH_DEFAULT', TEMP_FILEBEAT)
    @patch('filebeat_plugin.tasks.ctx', mock_install_ctx())
    def test_download_filebeat_path_not_exists(self):
        '''test download - verify nothing downloaded'''
        filename = tasks.download_filebeat(
            'https://download.elastic.co/beats/filebeat/' +
            'filebeat_1.2.3_amd64.deb',
            TEMP_FILEBEAT)

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
        os.mkdir(TEMP_FILEBEAT)

        filename = tasks._download_file(
            'https://download.elastic.co/beats/filebeat/' +
            'filebeat_1.2.3_amd64.deb',
            TEMP_FILEBEAT)
        self.assertEqual(filename, 'filebeat_1.2.3_amd64.deb')
        self.assertTrue(os.path.exists(filename))

    @patch('filebeat_plugin.tasks.FILEBEAT_CONFIG_FILE_DEFAULT', CONFIG_FILE)
    @patch('filebeat_plugin.tasks.FILEBEAT_PATH_DEFAULT', TEMP_FILEBEAT)
    @patch('filebeat_plugin.tasks.ctx', mock_install_ctx())
    def test_download_file_failed(self):
        '''test download - verify nothing downloaded'''
        os.mkdir(TEMP_FILEBEAT)

        self.assertRaises(ValueError, tasks._download_file, None, None)
