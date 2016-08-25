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

from cosmo_tester.framework.testenv import TestCase
import subprocess
import os

class FilebeatTest(TestCase):

    def test_filebeat_plugin(self):

        blueprint_path = self.copy_blueprint('resources', os.path.dirname(__file__))
        self.blueprint_yaml = os.path.join(blueprint_path, 'blueprint.yaml')

        self.upload_deploy_and_execute_install()

        outputs = self.client.deployments.outputs.get(self.test_id)
        outputs = outputs['outputs']
        ip = outputs['ip']
        self.verify_results(ip)

        self.execute_uninstall()

    def verify_results(self, ip):
        cmd = "curl -XGET 'http://{0}:9200/_all/_search'".format(ip)
        data = subprocess.check_output(cmd, shell=True)
        self.assertIn('logging', data)
