#!/usr/bin/python 
# -*- coding: utf-8 -*-

# Copyright: (c) 2021, Andrew Heath <aheath1992@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
author:
 - Andrew Heath (@aheath1992)
module: insights_user
short_description: Adds or removes users from groups.
description:
 - This module is allows you to add or remove users from a group in cloud.redhat.com.
   this module utilizes the cloud.redhat.com referenced here.
   https://console.redhat.com/docs/api
options:
  name:
    description:
      - Username of the user which you want to add to a group.
    type: str
    required: True
  group:
    description:
      - Group you wish to add the user to.
    type: str
    required: True
  state:
    description:
      - Whether to ensure the user is added or removed from the group.
    type: str
    choices: [absent, present]
    default: present
  username:
    description:
      - Username to authenticate to the API endpoint.
    type: str
    required: True
  password:
    description:
      - Password to authenticate to the API endpoint.
    type: str
    required: True
'''
EXAMPLES = r'''
- name: Add user to group
  insights_user:
    name: username
    group: foobar
    state: present
    username: Username
    password: Password

- name: Remove user to group
  insights_user:
    name: username
    group: foobar
    state: absent
    username: Username
    password: Password
'''
import json
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import open_url, ConnectionError, SSLValidationError

class Users(object):
    def __init__(self, module):
        self.module = module
        self.name = module.params['name']
        self.state = module.params['state']
        self.group = module.params['group']
        self.username = module.params['username']
        self.password = module.params['password']
        self.verifySsl = True
        self.basicAuth = True

        self.id = self.getID(self.group)

    def getID(self, name):
        url = "https://console.redhat.com/api/rbac/v1/groups/"
        headers = {
            'Accept': "application/json",
            'User-Agent': 'Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:94.0) Gecko/20100101 Firefox/94.0'
        }
        response = open_url(url, method="GET", headers=headers, url_username=self.username, url_password=self.password, validate_certs=self.verifySsl, force_basic_auth=self.basicAuth)
        results = json.loads(response.read())
        for group in results['data']:
            if name == group['name']:
                return group['uuid']
        return False

    def user_exist(self, name):
        url = "https://console.redhat.com/api/rbac/v1/groups/{uuid}/principals/".format(uuid=self.id)
        headers = {
            'Accept': "application/json",
            'User-Agent': 'Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:94.0) Gecko/20100101 Firefox/94.0'
        }
        response = open_url(url, method="GET", headers=headers, url_username=self.username, url_password=self.password, validate_certs=self.verifySsl, force_basic_auth=self.basicAuth)
        results = json.loads(response.read())
        for user in results['data']:
            if name == user['username']:
                return True
        return False

    def user_add(self):
        url = "https://console.redhat.com/api/rbac/v1/groups/{uuid}/principals/".format(uuid=self.id)
        headers = {
            'Accept': "application/json",
            'Content-Type': "application/json",
            'User-Agent': 'Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:94.0) Gecko/20100101 Firefox/94.0'
        }
        data = {
                'principals': [
                    {
                      'username': self.name
                    }
                ]
        }
        json_data = json.dumps(data, ensure_ascii=False)
        try:
            open_url(url, method="POST", headers=headers, url_username=self.username, url_password=self.password, data=json_data, validate_certs=self.verifySsl, force_basic_auth=self.basicAuth)
            return 0, f"User {self.name} was added to group {self.group}", ""
        except:
            return 1, f"User {self.name} was not added", ""

    def user_delete(self):
        url = "https://console.redhat.com/api/rbac/v1/groups/{uuid}/principals/?usernames={username}".format(uuid=self.id, username=self.name)
        headers = {
            'Accept': "application/json",
            'User-Agent': 'Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:94.0) Gecko/20100101 Firefox/94.0'
        }
        try:
            open_url(url, method="DELETE", headers=headers, url_username=self.username, url_password=self.password, validate_certs=self.verifySsl, force_basic_auth=self.basicAuth)
            return 0, f"User {self.name} is deleted from the API server", ""
        except:
            return 1, f"User {self.name} is not deleted", "Some error occurred when doing the HTTP request to the API server"

def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', default='present',
                       choices=['absent', 'present']),
            name=dict(type='str', required=True),
            group=dict(type='str', required=True),
            username=dict(required=False),
            password=dict(required=False, no_log=True),
        ),
        supports_check_mode=False,
    )

    api = Users(module)

    rc = None
    out = ''
    err = ''
    result = {}
    result['name'] = api.name
    result['state'] = api.state

    # TODO logic to do something based on the state:
    if api.state == 'absent':
        if api.user_exist(api.name):
            # do something to delete user
            rc, out, err = api.user_delete()
    elif api.state == 'present':
        if not api.user_exist(api.name):
            # do something to add user
            rc, out, err = api.user_add()
    if rc is not None and rc != 0:
        err = "Something bad happend"
        module.fail_json(name=api.name, msg=err)

    if rc is None:
        result['changed'] = False
    else:
        result['changed'] = True
    if out:
        result['stdout'] = out
    if err:
        result['stderr'] = err

    module.exit_json(**result)



if __name__ == '__main__':
    main()
