# List Running EC2 instances and stop those AWS EC2 instances.
import boto3

def lambda_handler(event, context):
    ec2 = boto3.resource('ec2')
    instances = ec2.instances.filter(
        Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
    for instance in instances:
        instance.stop()
        print('Stopped instance: ', instance.id)