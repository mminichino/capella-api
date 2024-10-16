##

import time
import attr
import os
import logging
import warnings
import configparser
import base64
import hashlib
import json
import sqlite3
import botocore.exceptions
import boto3
import google.auth
import google.auth.impersonated_credentials
import googleapiclient.discovery
import google.auth.transport.requests
import googleapiclient.errors
from azure.identity import AzureCliCredential
from azure.mgmt.resource.subscriptions import SubscriptionClient
from azure.core.exceptions import ResourceNotFoundError
from azure.mgmt.network.models import VirtualNetwork
from azure.mgmt.network import NetworkManagementClient
from google.cloud import resourcemanager_v3
from typing import Iterable, Union
from attr.validators import instance_of as io
from pathlib import Path

warnings.filterwarnings("ignore")
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
logger = logging.getLogger('tests.common')
logger.addHandler(logging.NullHandler())
logging.getLogger("docker").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

local_config_file = os.path.join(Path.home(), '.capella', 'credentials')
aws_region = 'us-east-1'
gcp_region = 'us-central1'
azure_region = 'eastus'


def short_hash(text: str) -> str:
    hasher = hashlib.sha1(text.encode())
    return base64.urlsafe_b64encode(hasher.digest()[:4]).decode().replace('=', '').lower()


@attr.s
class AWSTag(object):
    Key = attr.ib(validator=io(str))
    Value = attr.ib(validator=io(str))

    @property
    def as_dict(self):
        return self.__dict__


@attr.s
class AWSTagStruct(object):
    ResourceType = attr.ib(validator=io(str))
    Tags = attr.ib(validator=io(Iterable))

    @classmethod
    def build(cls, resource: str):
        return cls(
            resource,
            []
        )

    def add(self, obj: AWSTag):
        self.Tags.append(obj.as_dict)
        return self

    @property
    def as_dict(self):
        return self.__dict__


def get_account_email():
    if os.environ.get('CAPELLA_USER_EMAIL'):
        return os.environ.get('CAPELLA_USER_EMAIL')
    elif os.path.exists(local_config_file):
        config_data = configparser.ConfigParser()
        config_data.read(local_config_file)
        if 'default' in config_data:
            pytest_config = config_data['default']
            if pytest_config.get('account_email'):
                return pytest_config.get('account_email')
    else:
        return None


def aws_account_id():
    sts_client = boto3.client('sts')
    return sts_client.get_caller_identity()["Account"]


def get_aws_vpc(vpc_name: str, vpc_cidr: str):
    ec2_client = boto3.client('ec2', region_name=aws_region)
    vpc_filter = [
        {
            'Name': 'tag:Name',
            'Values': [
                vpc_name
            ]
        },
        {
            'Name': "cidr",
            'Values': [
                vpc_cidr,
            ]
        }
    ]
    try:
        result = ec2_client.describe_vpcs(Filters=vpc_filter)
        return result['Vpcs']
    except botocore.exceptions.ClientError as err:
        if err.response['Error']['Code'].endswith('NotFound'):
            return []
        raise RuntimeError(f"ClientError: {err}")
    except Exception as err:
        raise RuntimeError(f"error getting VPC details: {err}")


def create_aws_vpc(name: str, cidr: str, tags: dict = None) -> str:
    ec2_client = boto3.client('ec2', region_name=aws_region)
    vpc_tag = AWSTagStruct.build("vpc")
    vpc_tag.add(AWSTag("Name", name))
    if tags:
        for k, v in tags.items():
            vpc_tag.add(AWSTag(k, str(v)))
    try:
        result = ec2_client.create_vpc(CidrBlock=cidr, TagSpecifications=[vpc_tag.as_dict])
    except Exception as err:
        raise RuntimeError(f"error creating VPC: {err}")

    return result['Vpc']['VpcId']


def delete_aws_vpc(vpc_id: str) -> None:
    ec2_client = boto3.client('ec2', region_name=aws_region)
    try:
        ec2_client.delete_vpc(VpcId=vpc_id)
    except botocore.exceptions.ClientError as err:
        if err.response['Error']['Code'].endswith('NotFound'):
            return
        raise RuntimeError(f"ClientError: {err}")
    except Exception as err:
        raise RuntimeError(f"error deleting VPC: {err}")


def get_aws_vpc_peer(peer_id: str) -> dict:
    ec2_client = boto3.client('ec2', region_name=aws_region)
    try:
        result = ec2_client.describe_vpc_peering_connections(VpcPeeringConnectionIds=[peer_id])
        return result['VpcPeeringConnections'][0]
    except botocore.exceptions.ClientError as err:
        raise RuntimeError(f"ClientError: {err}")
    except Exception as err:
        raise RuntimeError(f"error accepting peering request: {err}")


def aws_vpc_peering_accept(peer_id: str):
    ec2_client = boto3.client('ec2', region_name=aws_region)
    try:
        ec2_client.accept_vpc_peering_connection(VpcPeeringConnectionId=peer_id)
    except botocore.exceptions.ClientError as err:
        raise RuntimeError(f"ClientError: {err}")
    except Exception as err:
        raise RuntimeError(f"error accepting peering request: {err}")


def aws_hosted_zone_associations(vpc_id: str, region: str):
    dns_client = boto3.client('route53')
    extra_args = {}
    results = []
    try:
        while True:
            result = dns_client.list_hosted_zones_by_vpc(VPCId=vpc_id, VPCRegion=region, **extra_args)
            results.extend(result['HostedZoneSummaries'])
            if 'NextToken' not in result:
                break
            extra_args['NextToken'] = result['NextToken']
        return results
    except Exception as err:
        raise RuntimeError(f"error getting VPC list: {err}")


def aws_associate_hosted_zone(hosted_zone: str, vpc_id: str, region: str):
    dns_client = boto3.client('route53')
    current_associations = aws_hosted_zone_associations(vpc_id, region)
    if next((z for z in current_associations if z.get('HostedZoneId') == hosted_zone), None):
        return
    vpc_info = {
        'VPCRegion': region,
        'VPCId': vpc_id
    }
    try:
        result = dns_client.associate_vpc_with_hosted_zone(HostedZoneId=hosted_zone, VPC=vpc_info)
        return result.get('ChangeInfo', {}).get('Status')
    except Exception as err:
        raise RuntimeError(f"error associating hosted zone: {err}")


gcp_credentials = None
gcp_project_id = None
gcp_service_account_email = None
gcp_account_email = None


def gcp_authenticate():
    global gcp_credentials, gcp_project_id, gcp_service_account_email, gcp_account_email
    try:
        gcp_credentials, gcp_project_id = google.auth.default()

        if hasattr(gcp_credentials, "service_account_email"):
            gcp_service_account_email = gcp_credentials.service_account_email
            gcp_account_email = None
        elif hasattr(gcp_credentials, "signer_email"):
            gcp_service_account_email = gcp_credentials.signer_email
            gcp_account_email = None
        else:
            gcp_service_account_email = None
            request = google.auth.transport.requests.Request()
            gcp_credentials.refresh(request=request)
            token_payload = gcp_credentials.id_token.split('.')[1]
            input_bytes = token_payload.encode('utf-8')
            rem = len(input_bytes) % 4
            if rem > 0:
                input_bytes += b"=" * (4 - rem)
            json_data = base64.urlsafe_b64decode(input_bytes).decode('utf-8')
            token_data = json.loads(json_data)
            gcp_account_email = token_data.get('email')
    except Exception as err:
        raise RuntimeError(f"error connecting to GCP: {err}")


def gcp_get_config_dir():
    if 'CLOUDSDK_CONFIG' in os.environ:
        return os.environ['CLOUDSDK_CONFIG']
    if os.name != 'nt':
        return os.path.join(Path.home(), '.config', 'gcloud')
    if 'APPDATA' in os.environ:
        return os.path.join(os.environ['APPDATA'], 'gcloud')
    drive = os.environ.get('SystemDrive', 'C:')
    return os.path.join(drive, os.path.sep, 'gcloud')


def gcp_get_account(account: str):
    account_db = os.path.join(gcp_get_config_dir(), 'credentials.db')
    connection = sqlite3.connect(
        account_db,
        detect_types=sqlite3.PARSE_DECLTYPES,
        isolation_level=None,
        check_same_thread=True
    )

    cursor = connection.cursor()
    table = cursor.execute('SELECT account_id, value FROM credentials').fetchall()
    for row in table:
        account_id, cred_json = row[0], row[1]
        if account_id == account:
            return json.loads(cred_json)

    return None


def gcp_sa_auth(service_account_email):
    auth_data = gcp_get_account(service_account_email)
    if not auth_data:
        raise RuntimeError(f"Account {service_account_email} is not configured. Use gcloud auth to add the account.")
    credentials, _ = google.auth.load_credentials_from_dict(auth_data)
    return credentials


def gcp_project():
    return gcp_project_id


def gcp_project_number():
    rm = resourcemanager_v3.ProjectsClient()
    req = resourcemanager_v3.GetProjectRequest(dict(name=f"projects/{gcp_project_id}"))
    res = rm.get_project(request=req)
    project_number = res.name.split('/')[1]
    return project_number


def gcp_compute_default_sa():
    project_number = gcp_project_number()
    return f"{project_number}-compute@developer.gserviceaccount.com"


def gcp_get_network(network: str) -> Union[dict, None]:
    gcp_client = googleapiclient.discovery.build('compute', 'v1', credentials=gcp_credentials)
    try:
        request = gcp_client.networks().get(project=gcp_project_id, network=network)
        result = request.execute()
        return result
    except googleapiclient.errors.HttpError as err:
        error_details = err.error_details[0].get('reason')
        if error_details != "notFound":
            raise RuntimeError(f"can not find network: {err}")
        return None
    except Exception as err:
        raise RuntimeError(f"error getting network: {err}")


def gcp_network_create(name: str) -> str:
    gcp_client = googleapiclient.discovery.build('compute', 'v1', credentials=gcp_credentials)
    operation = {}
    network_body = {
        "name": name,
        "autoCreateSubnetworks": False
    }
    try:
        request = gcp_client.networks().insert(project=gcp_project_id, body=network_body)
        operation = request.execute()
        gcp_wait_for_global_operation(operation['name'])
        return operation.get('targetLink')
    except googleapiclient.errors.HttpError as err:
        error_details = err.error_details[0].get('reason')
        if error_details != "alreadyExists":
            raise RuntimeError(f"can not create network: {err}")
    except Exception as err:
        raise RuntimeError(f"error creating network: {err}")

    return operation.get('targetLink')


def gcp_subnet_create(name: str, network_link: str, cidr: str) -> str:
    gcp_client = googleapiclient.discovery.build('compute', 'v1', credentials=gcp_credentials)
    operation = {}
    subnetwork_body = {
        "name": name,
        "network": network_link,
        "ipCidrRange": cidr,
        "region": gcp_region
    }
    try:
        request = gcp_client.subnetworks().insert(project=gcp_project_id, region=gcp_region, body=subnetwork_body)
        operation = request.execute()
        gcp_wait_for_regional_operation(operation['name'])
    except googleapiclient.errors.HttpError as err:
        error_details = err.error_details[0].get('reason')
        if error_details != "alreadyExists":
            raise RuntimeError(f"can not create subnet: {err}")
    except Exception as err:
        raise RuntimeError(f"error creating subnet: {err}")

    return operation.get('targetLink')


def gcp_network_delete(network: str) -> None:
    gcp_client = googleapiclient.discovery.build('compute', 'v1', credentials=gcp_credentials)
    try:
        request = gcp_client.networks().delete(project=gcp_project_id, network=network)
        operation = request.execute()
        gcp_wait_for_global_operation(operation['name'])
    except googleapiclient.errors.HttpError as err:
        error_details = err.error_details[0].get('reason')
        if error_details != "notFound":
            raise RuntimeError(f"can not delete network: {err}")
    except Exception as err:
        raise RuntimeError(f"error deleting network: {err}")


def gcp_add_peering(name: str, network: str, peer_project: str, peer_network: str) -> None:
    gcp_client = googleapiclient.discovery.build('compute', 'v1', credentials=gcp_credentials)
    peering_body = {
        "networkPeering": {
            "name": name,
            "network": f"projects/{peer_project}/global/networks/{peer_network}",
            "exchangeSubnetRoutes": True
        }
    }
    try:
        request = gcp_client.networks().addPeering(project=gcp_project_id, network=network, body=peering_body)
        operation = request.execute()
        gcp_wait_for_global_operation(operation['name'])
    except googleapiclient.errors.HttpError as err:
        error_details = err.error_details[0].get('reason')
        if error_details != "alreadyExists":
            raise RuntimeError(f"can not add network peering: {err}")
    except Exception as err:
        raise RuntimeError(f"error adding network peering: {err}")


def gcp_remove_peering(name: str, network: str) -> None:
    gcp_client = googleapiclient.discovery.build('compute', 'v1', credentials=gcp_credentials)
    remove_body = {
        "name": name
    }
    try:
        request = gcp_client.networks().removePeering(project=gcp_project_id, network=network, body=remove_body)
        operation = request.execute()
        gcp_wait_for_global_operation(operation['name'])
    except googleapiclient.errors.HttpError as err:
        error_details = err.error_details[0].get('reason')
        if error_details != "notFound":
            raise RuntimeError(f"can not remove network peering: {err}")
    except Exception as err:
        raise RuntimeError(f"error removing network peering: {err}")


def fqdn(domain: str):
    if domain[-1] not in ['.']:
        domain = domain + '.'
    return domain


def gcp_create_managed_zone(name: str,
                            domain: str,
                            network_link: str = None,
                            private: bool = False,
                            peer_project: str = None,
                            peer_network: str = None,
                            service_account: str = None):
    if service_account:
        dns_client = googleapiclient.discovery.build('dns', 'v1', credentials=gcp_sa_auth(service_account))
    else:
        dns_client = googleapiclient.discovery.build('dns', 'v1', credentials=gcp_credentials)
    visibility = 'private' if private else 'public'
    dns_body = {
        'kind': 'dns#managedZone',
        'name': name,
        'dnsName': fqdn(domain),
        'description': 'Couch Formation Managed Zone',
        'visibility': visibility
    }
    if private and network_link:
        dns_body['privateVisibilityConfig'] = {
            "kind": "dns#managedZonePrivateVisibilityConfig",
            "networks": [
                {
                    "kind": "dns#managedZonePrivateVisibilityConfigNetwork",
                    "networkUrl": network_link
                }
            ]
        }
    if peer_project and peer_network:
        dns_body['peeringConfig'] = {
            "targetNetwork": {
                "networkUrl": f"https://www.googleapis.com/compute/v1/projects/{peer_project}/global/networks/{peer_network}",
                "kind": "dns#managedZonePeeringConfigTargetNetwork"
            },
            "kind": "dns#managedZonePeeringConfig"
        }

    try:
        request = dns_client.managedZones().create(project=gcp_project_id, body=dns_body)
        result = request.execute()
        return result.get('name')
    except googleapiclient.errors.HttpError as err:
        error_details = err.error_details[0].get('reason')
        if error_details != "alreadyExists":
            raise RuntimeError(f"can not create managed zone: {err}")
        return name
    except Exception as err:
        raise RuntimeError(f"error creating managed zone: {err}")


def gcp_delete_managed_zone(name: str):
    dns_client = googleapiclient.discovery.build('dns', 'v1', credentials=gcp_credentials)
    try:
        request = dns_client.managedZones().delete(project=gcp_project_id, managedZone=name)
        request.execute()
    except googleapiclient.errors.HttpError as err:
        error_details = err.error_details[0].get('reason')
        if error_details != "notFound":
            raise RuntimeError(f"can not delete managed zone: {err}")
    except Exception as err:
        raise RuntimeError(f"error deleting managed zone: {err}")


def gcp_subnet_delete(subnet: str) -> None:
    gcp_client = googleapiclient.discovery.build('compute', 'v1', credentials=gcp_credentials)
    try:
        request = gcp_client.subnetworks().delete(project=gcp_project_id, region=gcp_region, subnetwork=subnet)
        operation = request.execute()
        gcp_wait_for_regional_operation(operation['name'])
    except googleapiclient.errors.HttpError as err:
        error_details = err.error_details[0].get('reason')
        if error_details != "notFound":
            raise RuntimeError(f"can not delete subnet: {err}")
    except Exception as err:
        raise RuntimeError(f"error deleting subnet: {err}")


def gcp_wait_for_global_operation(operation):
    gcp_client = googleapiclient.discovery.build('compute', 'v1', credentials=gcp_credentials)
    while True:
        result = gcp_client.globalOperations().get(
            project=gcp_project_id,
            operation=operation).execute()

        if result['status'] == 'DONE':
            if 'error' in result:
                raise RuntimeError(result['error'])
            return result

        time.sleep(1)


def gcp_wait_for_regional_operation(operation):
    gcp_client = googleapiclient.discovery.build('compute', 'v1', credentials=gcp_credentials)
    while True:
        result = gcp_client.regionOperations().get(
            project=gcp_project_id,
            region=gcp_region,
            operation=operation).execute()

        if result['status'] == 'DONE':
            if 'error' in result:
                raise RuntimeError(result['error'])
            return result

        time.sleep(1)


azure_credential = None
azure_tenant_id = ""
azure_subscription_id = ""


def azure_authenticate():
    global azure_credential, azure_tenant_id, azure_subscription_id
    try:
        azure_credential = AzureCliCredential()
        token = azure_credential.get_token("https://management.azure.com/", scopes=["user.read"])
        base64_meta_data = token.token.split(".")[1].encode("utf-8") + b'=='
        json_bytes = base64.decodebytes(base64_meta_data)
        json_string = json_bytes.decode("utf-8")
        json_dict = json.loads(json_string)
        upn = json_dict.get("upn", "unavailableUpn")
        subscription_client = SubscriptionClient(azure_credential)
        subscriptions = subscription_client.subscriptions.list()
        azure_subscription_id = next((s.subscription_id for s in subscriptions), None)
        azure_principal_id = upn
        azure_tenant_id = json_dict["tid"]
        return azure_credential, azure_subscription_id, azure_tenant_id
    except Exception as err:
        raise RuntimeError(f"Azure: unauthorized (use az login): {err}")


def get_azure_tenant_id():
    return azure_tenant_id


def get_azure_subscription_id():
    return azure_subscription_id


def azure_get_network(network: str, resource_group: str) -> Union[VirtualNetwork, None]:
    network_client = NetworkManagementClient(azure_credential, azure_subscription_id)
    try:
        info = network_client.virtual_networks.get(resource_group, network)
        return info
    except ResourceNotFoundError:
        return None
    except Exception as err:
        raise RuntimeError(f"error getting vnet: {err}")


def azure_create_network(name: str, cidr: str, resource_group: str):
    network_client = NetworkManagementClient(azure_credential, azure_subscription_id)
    parameters = {
        'location': azure_region,
        'address_space': {
            'address_prefixes': [cidr]
        }
    }

    net_info = azure_get_network(name, resource_group)
    if net_info:
        return net_info

    try:
        request = network_client.virtual_networks.begin_create_or_update(resource_group, name, parameters)
        request.wait()
        return request.result()
    except Exception as err:
        raise RuntimeError(f"error creating network: {err}")


def azure_delete_network(network: str, resource_group: str) -> None:
    network_client = NetworkManagementClient(azure_credential, azure_subscription_id)
    try:
        request = network_client.virtual_networks.begin_delete(resource_group, network)
        request.wait()
    except ResourceNotFoundError:
        return None
    except Exception as err:
        raise RuntimeError(f"error getting vnet: {err}")
