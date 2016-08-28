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


from setuptools import setup

# Replace the place holders with values for your project

setup(

    # Do not use underscores in the plugin name.
    name='cloudify-filebeat-plugin',

    version='0.1',
    author='Gigaspaces',
    author_email='cosmo-admin@gigaspaces.com',
    description='plugin for running logging interface (based on Filebeats)',

    # This must correspond to the actual packages in the plugin.
    packages=['filebeat_plugin'],
    package_data={'filebeat_plugin': ['resources/filebeat.yml']},
    license='LICENSE',
    zip_safe=False,
    install_requires=[
        # Necessary dependency for developing plugins, do not remove!
        'cloudify-plugins-common>=3.4m5',  'distro==0.6.0'
    ],
    test_requires=[
        'cloudify-dsl-parser>=3.4m5', 'nose',
    ]
)
