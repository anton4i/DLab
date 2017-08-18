#!/usr/bin/python

# *****************************************************************************
#
# Copyright (c) 2016, EPAM SYSTEMS INC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# ******************************************************************************

import json
from dlab.fab import *
from dlab.meta_lib import *
import sys, time, os
from dlab.actions_lib import *
import traceback
from Crypto.PublicKey import RSA


if __name__ == "__main__":
    local_log_filename = "{}_{}_{}.log".format(os.environ['conf_resource'], os.environ['edge_user_name'], os.environ['request_id'])
    local_log_filepath = "/logs/edge/" + local_log_filename
    logging.basicConfig(format='%(levelname)-8s [%(asctime)s]  %(message)s',
                        level=logging.DEBUG,
                        filename=local_log_filepath)

    print 'Generating infrastructure names and tags'
    edge_conf = dict()
    edge_conf['service_base_name'] = os.environ['conf_service_base_name']
    edge_conf['key_name'] = os.environ['conf_key_name']
    edge_conf['user_keyname'] = os.environ['edge_user_name']
    edge_conf['vpc_name'] = os.environ['azure_vpc_name']
    edge_conf['subnet_name'] = os.environ['azure_subnet_name']
    edge_conf['private_subnet_name'] = edge_conf['service_base_name'] + '-' + os.environ['edge_user_name'] + '-subnet'
    edge_conf['network_interface_name'] = edge_conf['service_base_name'] + "-" + os.environ['edge_user_name'] + \
                                          '-edge-nif'
    edge_conf['static_public_ip_name'] = edge_conf['service_base_name'] + "-" + os.environ['edge_user_name'] + \
                                         '-edge-ip'
    edge_conf['region'] = os.environ['azure_region']
    edge_conf['vpc_cidr'] = '10.10.0.0/16'
    edge_conf['private_subnet_prefix'] = os.environ['azure_private_subnet_prefix']
    edge_conf['instance_name'] = edge_conf['service_base_name'] + "-" + os.environ['edge_user_name'] + '-edge'
    edge_conf['edge_security_group_name'] = edge_conf['instance_name'] + '-sg'
    edge_conf['notebook_security_group_name'] = edge_conf['service_base_name'] + "-" + os.environ[
        'edge_user_name'] + '-nb-sg'
    edge_conf['edge_container_name'] = (edge_conf['service_base_name'] + '-' + os.environ['edge_user_name']).lower().\
        replace('_', '-')
    edge_conf['storage_account_name'] = (edge_conf['service_base_name'] + os.environ['edge_user_name']).lower().\
        replace('_', '').replace('-', '')
    ssh_key_path = '/root/keys/' + os.environ['conf_key_name'] + '.pem'
    key = RSA.importKey(open(ssh_key_path, 'rb').read())
    edge_conf['public_ssh_key'] = key.publickey().exportKey("OpenSSH")

    # FUSE in case of absence of user's key
    fname = "/root/keys/{}.pub".format(edge_conf['user_keyname'])
    if not os.path.isfile(fname):
        print "USERs PUBLIC KEY DOES NOT EXIST in {}".format(fname)
        sys.exit(1)

    print "Will create exploratory environment with edge node as access point as following: " + \
          json.dumps(edge_conf, sort_keys=True, indent=4, separators=(',', ': '))
    logging.info(json.dumps(edge_conf))

    try:
        logging.info('[CREATE SUBNET]')
        print '[CREATE SUBNET]'
        params = "--resource_group_name {} --vpc_name {} --region {} --vpc_cidr {} --subnet_name {} --prefix {}".\
            format(edge_conf['service_base_name'], edge_conf['vpc_name'], edge_conf['region'], edge_conf['vpc_cidr'],
                   edge_conf['private_subnet_name'], edge_conf['private_subnet_prefix'])
        try:
            local("~/scripts/{}.py {}".format('common_create_subnet', params))
        except:
            traceback.print_exc()
            raise Exception
    except Exception as err:
        try:
            AzureActions().remove_subnet(edge_conf['service_base_name'], edge_conf['vpc_name'],
                                         edge_conf['private_subnet_name'])
        except:
            print "Subnet hasn't been created."
        append_result("Failed to create subnet.", str(err))
        sys.exit(1)

    edge_conf['private_subnet_cidr'] = AzureMeta().get_subnet(edge_conf['service_base_name'], edge_conf['vpc_name'],
                                                              edge_conf['subnet_name']).address_prefix
    print 'NEW SUBNET CIDR CREATED: {}'.format(edge_conf['private_subnet_cidr'])

    # try:
    #     logging.info('[CREATE EDGE ROLES]')
    #     print '[CREATE EDGE ROLES]'
    #     params = "--role_name {} --role_profile_name {} --policy_name {} --region {}" \
    #              .format(edge_conf['role_name'], edge_conf['role_profile_name'],
    #                      edge_conf['policy_name'], os.environ['aws_region'])
    #     try:
    #         local("~/scripts/{}.py {}".format('common_create_role_policy', params))
    #     except:
    #         traceback.print_exc()
    #         raise Exception
    # except Exception as err:
    #     append_result("Failed to creating roles.", str(err))
    #     sys.exit(1)
    #
    # try:
    #     logging.info('[CREATE BACKEND (NOTEBOOK) ROLES]')
    #     print '[CREATE BACKEND (NOTEBOOK) ROLES]'
    #     params = "--role_name {} --role_profile_name {} --policy_name {} --region {}" \
    #              .format(edge_conf['notebook_role_name'], edge_conf['notebook_role_profile_name'],
    #                      edge_conf['notebook_policy_name'], os.environ['aws_region'])
    #     try:
    #         local("~/scripts/{}.py {}".format('common_create_role_policy', params))
    #     except:
    #         traceback.print_exc()
    #         raise Exception
    # except Exception as err:
    #     append_result("Failed to creating roles.", str(err))
    #     remove_all_iam_resources('edge', os.environ['edge_user_name'])
    #     sys.exit(1)

    try:
        logging.info('[CREATE SECURITY GROUP FOR EDGE NODE]')
        print '[CREATE SECURITY GROUP FOR EDGE]'
        list_rules = [
            {
                "name": "in-1",
                "protocol": "*",
                "source_port_range": "*",
                "destination_port_range": "*",
                "source_address_prefix": edge_conf['private_subnet_cidr'],
                "destination_address_prefix": "*",
                "access": "Allow",
                "priority": 100,
                "direction": "Inbound"
            },
            {
                "name": "in-2",
                "protocol": "Tcp",
                "source_port_range": "22",
                "destination_port_range": "*",
                "source_address_prefix": "0.0.0.0/0",
                "destination_address_prefix": "*",
                "access": "Allow",
                "priority": 101,
                "direction": "Inbound"
            },
            {
                "name": "out-1",
                "protocol": "Tcp",
                "source_port_range": "22",
                "destination_port_range": "*",
                "source_address_prefix": edge_conf['private_subnet_cidr'],
                "destination_address_prefix": "*",
                "access": "Allow",
                "priority": 100,
                "direction": "Outbound"
            },
            {
                "name": "out-2",
                "protocol": "Tcp",
                "source_port_range": "8888",
                "destination_port_range": "8888",
                "source_address_prefix": edge_conf['private_subnet_cidr'],
                "destination_address_prefix": "*",
                "access": "Allow",
                "priority": 101,
                "direction": "Outbound"
            },
            {
                "name": "out-3",
                "protocol": "Tcp",
                "source_port_range": "8080",
                "destination_port_range": "8080",
                "source_address_prefix": edge_conf['private_subnet_cidr'],
                "destination_address_prefix": "*",
                "access": "Allow",
                "priority": 102,
                "direction": "Outbound"
            },
            {
                "name": "out-4",
                "protocol": "Tcp",
                "source_port_range": "8787",
                "destination_port_range": "8787",
                "source_address_prefix": edge_conf['private_subnet_cidr'],
                "destination_address_prefix": "*",
                "access": "Allow",
                "priority": 103,
                "direction": "Outbound"
            },
            {
                "name": "out-5",
                "protocol": "Tcp",
                "source_port_range": "6006",
                "destination_port_range": "6006",
                "source_address_prefix": edge_conf['private_subnet_cidr'],
                "destination_address_prefix": "*",
                "access": "Allow",
                "priority": 104,
                "direction": "Outbound"
            },
            {
                "name": "out-6",
                "protocol": "Tcp",
                "source_port_range": "20888",
                "destination_port_range": "20888",
                "source_address_prefix": edge_conf['private_subnet_cidr'],
                "destination_address_prefix": "*",
                "access": "Allow",
                "priority": 105,
                "direction": "Outbound"
            },
            {
                "name": "out-7",
                "protocol": "Tcp",
                "source_port_range": "8088",
                "destination_port_range": "8088",
                "source_address_prefix": edge_conf['private_subnet_cidr'],
                "destination_address_prefix": "*",
                "access": "Allow",
                "priority": 106,
                "direction": "Outbound"
            },
            {
                "name": "out-8",
                "protocol": "Tcp",
                "source_port_range": "18080",
                "destination_port_range": "18080",
                "source_address_prefix": edge_conf['private_subnet_cidr'],
                "destination_address_prefix": "*",
                "access": "Allow",
                "priority": 107,
                "direction": "Outbound"
            },
            {
                "name": "out-9",
                "protocol": "Tcp",
                "source_port_range": "50070",
                "destination_port_range": "50070",
                "source_address_prefix": edge_conf['private_subnet_cidr'],
                "destination_address_prefix": "*",
                "access": "Allow",
                "priority": 108,
                "direction": "Outbound"
            },
            {
                "name": "out-10",
                "protocol": "Udp",
                "source_port_range": "53",
                "destination_port_range": "53",
                "source_address_prefix": '0.0.0.0/0',
                "destination_address_prefix": "*",
                "access": "Allow",
                "priority": 109,
                "direction": "Outbound"
            },
            {
                "name": "out-11",
                "protocol": "Tcp",
                "source_port_range": "80",
                "destination_port_range": "80",
                "source_address_prefix": '0.0.0.0/0',
                "destination_address_prefix": "*",
                "access": "Allow",
                "priority": 110,
                "direction": "Outbound"
            },
            {
                "name": "out-12",
                "protocol": "Tcp",
                "source_port_range": "22",
                "destination_port_range": "22",
                "source_address_prefix": '0.0.0.0/0',
                "destination_address_prefix": "*",
                "access": "Allow",
                "priority": 111,
                "direction": "Outbound"
            },
            {
                "name": "out-13",
                "protocol": "Tcp",
                "source_port_range": "443",
                "destination_port_range": "443",
                "source_address_prefix": '0.0.0.0/0',
                "destination_address_prefix": "*",
                "access": "Allow",
                "priority": 112,
                "direction": "Outbound"
            },
            {
                "name": "out-14",
                "protocol": "Tcp",
                "source_port_range": "8085",
                "destination_port_range": "8085",
                "source_address_prefix": edge_conf['private_subnet_cidr'],
                "destination_address_prefix": "*",
                "access": "Allow",
                "priority": 113,
                "direction": "Outbound"
            }
        ]
        params = "--resource_group_name {} --security_group_name {} --region {} --list_rules '{}'". \
            format(edge_conf['service_base_name'], edge_conf['edge_security_group_name'], edge_conf['region'],
                   json.dumps(list_rules))
        try:
            local("~/scripts/{}.py {}".format('common_create_security_group', params))
        except Exception as err:
            AzureActions().remove_subnet(edge_conf['service_base_name'], edge_conf['vpc_name'],
                                         edge_conf['private_subnet_name'])
            try:
                AzureActions().remove_security_group(edge_conf['service_base_name'],
                                                     edge_conf['edge_security_group_name'])
            except:
                print "Edge Security group hasn't been created."
            traceback.print_exc()
            append_result("Failed creating security group for edge node.", str(err))
            raise Exception
    except:
        sys.exit(1)

    try:
        logging.info('[CREATE SECURITY GROUP FOR PRIVATE SUBNET]')
        print '[CREATE SECURITY GROUP FOR PRIVATE SUBNET]'
        list_rules = [
            {
                "name": "in-1",
                "protocol": "*",
                "source_port_range": "*",
                "destination_port_range": "*",
                "source_address_prefix": edge_conf['private_subnet_cidr'],
                "destination_address_prefix": "*",
                "access": "Allow",
                "priority": 100,
                "direction": "Inbound"
            },
            {
                "name": "in-2",
                "protocol": "*",
                "source_port_range": "*",
                "destination_port_range": "*",
                "source_address_prefix": '{}/32'.format(AzureMeta().get_instance_private_ip_address(
                    edge_conf['service_base_name'], edge_conf['service_base_name'] + '-ssn')),
                "destination_address_prefix": "*",
                "access": "Allow",
                "priority": 101,
                "direction": "Inbound"
            },
            {
                "name": "out-1",
                "protocol": "*",
                "source_port_range": "*",
                "destination_port_range": "*",
                "source_address_prefix": edge_conf['private_subnet_cidr'],
                "destination_address_prefix": "*",
                "access": "Allow",
                "priority": 100,
                "direction": "Outbound"
            },
            {
                "name": "out-2",
                "protocol": "*",
                "source_port_range": "*",
                "destination_port_range": "*",
                "source_address_prefix": "0.0.0.0/0",
                "destination_address_prefix": "*",
                "access": "Allow",
                "priority": 101,
                "direction": "Outbound"
            },
            ]
        params = "--resource_group_name {} --security_group_name {} --region {} --list_rules '{}'". \
            format(edge_conf['service_base_name'], edge_conf['notebook_security_group_name'], edge_conf['region'],
                   json.dumps(list_rules))
        try:
            local("~/scripts/{}.py {}".format('common_create_security_group', params))
        except:
            traceback.print_exc()
            raise Exception
    except Exception as err:
        AzureActions().remove_subnet(edge_conf['service_base_name'], edge_conf['vpc_name'],
                                     edge_conf['private_subnet_name'])
        AzureActions().remove_security_group(edge_conf['service_base_name'], edge_conf['edge_security_group_name'])
        try:
            AzureActions().remove_security_group(edge_conf['service_base_name'],
                                                 edge_conf['notebook_security_group_name'])
        except:
            print "Notebook Security group hasn't been created."
        sys.exit(1)

    try:
        logging.info('[CREATE STORAGE ACCOUNT AND CONTAINERS]')
        print('[CREATE STORAGE ACCOUNT AND CONTAINERS]')

        params = "--container_name {} --account_name {} --resource_group_name {} --region {}". \
            format(edge_conf['edge_container_name'], edge_conf['storage_account_name'], edge_conf['service_base_name'],
                   edge_conf['region'])
        try:
            local("~/scripts/{}.py {}".format('common_create_container', params))
        except:
            traceback.print_exc()
            raise Exception
    except Exception as err:
        append_result("Failed to create bucket.", str(err))
        AzureActions().remove_subnet(edge_conf['service_base_name'], edge_conf['vpc_name'],
                                     edge_conf['private_subnet_name'])
        AzureActions().remove_security_group(edge_conf['service_base_name'], edge_conf['edge_security_group_name'])
        AzureActions().remove_security_group(edge_conf['service_base_name'], edge_conf['notebook_security_group_name'])
        try:
            AzureActions().remove_storage_account(edge_conf['service_base_name'], edge_conf['storage_account_name'])
        except:
            print "Storage account hasn't been created."
        sys.exit(1)

    # try:
    #     logging.info('[CREATING BUCKET POLICY FOR USER INSTANCES]')
    #     print('[CREATING BUCKET POLICY FOR USER INSTANCES]')
    #     params = '--bucket_name {} --ssn_bucket_name {} --shared_bucket_name {} --username {} --edge_role_name {} --notebook_role_name {} --service_base_name {} --region {}'.format(
    #         edge_conf['bucket_name'], edge_conf['ssn_bucket_name'], edge_conf['shared_bucket_name'], os.environ['edge_user_name'],
    #         edge_conf['role_name'], edge_conf['notebook_role_name'],  edge_conf['service_base_name'], edge_conf['region'])
    #     try:
    #         local("~/scripts/{}.py {}".format('common_create_policy', params))
    #     except:
    #         traceback.print_exc()
    # except Exception as err:
    #     append_result("Failed to create bucket policy.", str(err))
    #     remove_all_iam_resources('notebook', os.environ['edge_user_name'])
    #     remove_all_iam_resources('edge', os.environ['edge_user_name'])
    #     remove_sgroups(edge_conf['notebook_instance_name'])
    #     remove_sgroups(edge_conf['instance_name'])
    #     remove_s3('edge', os.environ['edge_user_name'])
    #     sys.exit(1)

    if os.environ['conf_os_family'] == 'debian':
        initial_user = 'ubuntu'
        sudo_group = 'sudo'
    if os.environ['conf_os_family'] == 'redhat':
        initial_user = 'ec2-user'
        sudo_group = 'wheel'

    try:
        logging.info('[CREATE EDGE INSTANCE]')
        print('[CREATE EDGE INSTANCE]')
        params = "--instance_name {} --instance_size {} --region {} --vpc_name {} --network_interface_name {} --security_group_name {} --subnet_name {} --service_base_name {} --dlab_ssh_user_name {} --public_ip_name {} --public_key '''{}''' --primary_disk_size {} --instance_type {} --user_name {}".\
            format(edge_conf['instance_name'], os.environ['azure_edge_instance_size'], edge_conf['region'],
                   edge_conf['vpc_name'], edge_conf['network_interface_name'], edge_conf['edge_security_group_name'],
                   edge_conf['subnet_name'], edge_conf['service_base_name'], initial_user,
                   edge_conf['static_public_ip_name'], edge_conf['public_ssh_key'], '30', 'edge',
                   os.environ['edge_user_name'])
        try:
            local("~/scripts/{}.py {}".format('common_create_instance', params))
        except:
            traceback.print_exc()
            raise Exception
    except Exception as err:
        AzureActions().remove_subnet(edge_conf['service_base_name'], edge_conf['vpc_name'],
                                     edge_conf['private_subnet_name'])
        AzureActions().remove_security_group(edge_conf['service_base_name'], edge_conf['edge_security_group_name'])
        AzureActions().remove_security_group(edge_conf['service_base_name'], edge_conf['notebook_security_group_name'])
        AzureActions().remove_storage_account(edge_conf['service_base_name'], edge_conf['storage_account_name'])
        try:
            AzureActions().remove_instance(edge_conf['service_base_name'], edge_conf['instance_name'])
            AzureActions().remove_instance(edge_conf['service_base_name'], edge_conf['static_public_ip_name'])
        except:
            print "The instance hasn't been created."
        append_result("Failed to create instance. Exception:" + str(err))
        sys.exit(1)