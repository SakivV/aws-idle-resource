import boto3
from datetime import datetime, timedelta

def lambda_handler(event, context):
    elbv2 = boto3.client('elbv2')
    cloudwatch = boto3.client('cloudwatch')
    
    # Fetch all load balancers
    load_balancers = elbv2.describe_load_balancers()

    for lb in load_balancers['LoadBalancers']:
        lb_name = lb['LoadBalancerName']

        # Get RequestCount metrics for the past 1 hour
        metrics = cloudwatch.get_metric_statistics(
            Namespace='AWS/ApplicationELB',
            MetricName='RequestCount',
            Dimensions=[
                {
                    'Name': 'LoadBalancer',
                    'Value': lb['LoadBalancerName']
                },
            ],
            StartTime=datetime.now() - timedelta(days=30),
            EndTime=datetime.now(),
            Period=3600,
            Statistics=['Sum'],
        )

        # Check if the load balancer is idle
        if not metrics['Datapoints'] or metrics['Datapoints'][0]['Sum'] == 0:
            print(f"Deleting idle Load Balancer: {lb_name}")

            # Delete the load balancer
            elbv2.delete_load_balancer(
                LoadBalancerArn=lb['LoadBalancerArn']
            )