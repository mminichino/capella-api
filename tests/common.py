##

import attr
import os
import logging
import warnings
import configparser
import botocore.exceptions
import boto3
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
