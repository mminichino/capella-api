##

import time
import attr
import os
import logging
import warnings
import configparser
import base64
import json
import botocore.exceptions
import boto3
import google.auth
import googleapiclient.discovery
import google.auth.transport.requests
import googleapiclient.errors
from google.cloud import resourcemanager_v3
from typing import Iterable
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
