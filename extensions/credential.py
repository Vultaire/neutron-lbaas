# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2011 Cisco Systems, Inc.  All rights reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#
# @author: Ying Liu, Cisco Systems, Inc.
#

import logging

from webob import exc
from extensions import _credential_view as credential_view
from extensions import _exceptions as exception
from extensions import _faults as faults

from quantum.api import api_common as common
from quantum.common import wsgi
from quantum.common import extensions
from quantum.manager import QuantumManager

LOG = logging.getLogger('quantum.api.credentials')


class Credential(object):

    def __init__(self):
        pass

    def get_name(self):
        return "Cisco Credential"

    def get_alias(self):
        return "Cisco Credential"

    def get_description(self):
        return "Credential include username and password"

    def get_namespace(self):
        return ""

    def get_updated(self):
        return "2011-07-25T13:25:27-06:00"

    def get_resources(self):
        parent_resource = dict(member_name="tenant",
                               collection_name="extensions/csco/tenants")
       
        controller = CredentialController(QuantumManager.get_plugin())
        return [extensions.ResourceExtension('credentials', controller,
                                             parent=parent_resource)]


class CredentialController(common.QuantumController):
    """ credential API controller
        based on QuantumController """

    _credential_ops_param_list = [{
        'param-name': 'credential_name',
        'required': True}, {
        'param-name': 'user_name',
        'required': True}, {
        'param-name': 'password',
        'required': True}]
   
    _serialization_metadata = {
        "application/xml": {
            "attributes": {
                "credential": ["id", "name"],
            },
        },
    }

    def __init__(self, plugin):
        self._resource_name = 'credential'
        super(CredentialController, self).__init__(plugin)
             
    def index(self, request, tenant_id):
        """ Returns a list of credential ids """
        #TODO: this should be for a given tenant!!!
        return self._items(request, tenant_id, is_detail=False)

    def _items(self, request, tenant_id, is_detail):
        """ Returns a list of credentials. """
        credentials = self._plugin.get_all_credentials(tenant_id)
        builder = credential_view.get_view_builder(request)
        result = [builder.build(credential, is_detail)['credential']
                  for credential in credentials]
        return dict(credentials=result)

    def show(self, request, tenant_id, id):
        """ Returns credential details for the given credential id """
        try:
            credential = self._plugin.get_credential_details(
                            tenant_id, id)
            builder = credential_view.get_view_builder(request)
            #build response with details
            result = builder.build(credential, True)
            return dict(credentials=result)
        except exception.CredentialNotFound as e:
            return faults.Fault(faults.CredentialNotFound(e))
                                
            #return faults.Fault(e)

    def create(self, request, tenant_id):
        """ Creates a new credential for a given tenant """
        #look for credential name in request
        try:
            req_params = \
                self._parse_request_params(request, 
                                           self._credential_ops_param_list)
        except exc.HTTPError as e:
            return faults.Fault(e)
        credential = self._plugin.\
                       create_credential(tenant_id,
                                          req_params['credential_name'],
                                          req_params['user_name'],
                                          req_params['password'])
        builder = credential_view.get_view_builder(request)
        result = builder.build(credential)
        return dict(credentials=result)

    def update(self, request, tenant_id, id):
        """ Updates the name for the credential with the given id """
        try:
            req_params = \
                self._parse_request_params(request, 
                                           self._credential_ops_param_list)
        except exc.HTTPError as e:
            return faults.Fault(e)
        try:
            credential = self._plugin.\
            rename_credential(tenant_id,
                        id, req_params['credential_name'])

            builder = credential_view.get_view_builder(request)
            result = builder.build(credential, True)
            return dict(credentials=result)
        except exception.CredentialNotFound as e:
            return faults.Fault(faults.CredentialNotFound(e))

    def delete(self, request, tenant_id, id):
        """ Destroys the credential with the given id """
        try:
            self._plugin.delete_credential(tenant_id, id)
            return exc.HTTPAccepted()
        except exception.CredentialNotFound as e:
            return faults.Fault(faults.CredentialNotFound(e))
        