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

import distro
from mock import patch

from cloudify.mocks import MockCloudifyContext
from .. import tasks


distro = distro.id()
TEMP_FILEBEAT = os.path.join(tempfile.gettempdir(), 'filebeat')


class TestFilebeatPlugin(unittest.TestCase):

    def setUp(self):
        os.mkdir(TEMP_FILEBEAT)

    def tearDown(self):
        # Remove filebeat temp dir
        if os.path.exists(TEMP_FILEBEAT):
            shutil.rmtree(TEMP_FILEBEAT)

    @patch('filebeat_plugin.tasks.FILEBEAT_PATH_DEFAULT', TEMP_FILEBEAT)
    @patch('filebeat_plugin.tasks.ctx', MockCloudifyContext())
    def test_download_filebeat(self):
        '''Test download_filebeat function
        '''

        filename = tasks.download_filebeat('', TEMP_FILEBEAT)
        if distro in ('ubuntu', 'debian'):
            self.assertEqual(filename, 'filebeat_1.2.3_amd64.deb')
        elif distro in ('centos', 'redhat'):
            self.assertEqual(filename, 'filebeat-1.2.3-x86_64.rpm')
        self.assertTrue(os.path.exists(os.path.join(TEMP_FILEBEAT, filename)))

    @patch('filebeat_plugin.tasks.FILEBEAT_PATH_DEFAULT', TEMP_FILEBEAT)
    @patch('filebeat_plugin.tasks.ctx', MockCloudifyContext())
    def test_download_filebeat_path_not_exists(self):
        '''Test download - verify nothing downloaded
        '''
        filename = tasks.download_filebeat(
            'https://download.elastic.co/beats/filebeat/' +
            'filebeat_1.2.3_amd64.deb',
            TEMP_FILEBEAT)

        if distro in ('ubuntu', 'debian'):
            self.assertEqual(filename, 'filebeat_1.2.3_amd64.deb')
        elif distro in ('centos', 'redhat'):
            self.assertEqual(filename, 'filebeat-1.2.3-x86_64.rpm')
        self.assertTrue(os.path.exists(os.path.join(TEMP_FILEBEAT, filename)))

    @patch('filebeat_plugin.tasks.FILEBEAT_PATH_DEFAULT', TEMP_FILEBEAT)
    @patch('filebeat_plugin.tasks.ctx', MockCloudifyContext())
    def test_download_file(self):
        '''Test download -  verify file exists after download
        '''

        filename = tasks._download_file(
            'https://download.elastic.co/beats/filebeat/' +
            'filebeat_1.2.3_amd64.deb',
            TEMP_FILEBEAT)
        self.assertEqual(filename, 'filebeat_1.2.3_amd64.deb')
        self.assertTrue(os.path.exists(filename))

    @patch('filebeat_plugin.tasks.FILEBEAT_PATH_DEFAULT', TEMP_FILEBEAT)
    @patch('filebeat_plugin.tasks.ctx', MockCloudifyContext())
    def test_download_file_failed(self):
        '''Test download - verify nothing downloaded
        '''

        self.assertRaises(ValueError, tasks._download_file, None, None)

    @patch('filebeat_plugin.tasks.FILEBEAT_PATH_DEFAULT', TEMP_FILEBEAT)
    @patch('filebeat_plugin.tasks.ctx', MockCloudifyContext())
    def test_run_command_(self):
        output = tasks._run('cd ~')
        self.assertEqual(output.returncode, 0)

    @patch('filebeat_plugin.tasks.FILEBEAT_PATH_DEFAULT', TEMP_FILEBEAT)
    @patch('filebeat_plugin.tasks.ctx', MockCloudifyContext())
    def test_run_command_failed(self):
        self.assertRaises(SystemExit, tasks._run, 'invalid command')