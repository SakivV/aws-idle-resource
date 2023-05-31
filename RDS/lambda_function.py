import boto3
from datetime import datetime, timedelta

def lambda_handler(event, context):
    rds = boto3.client('rds')
    cw = boto3.client('cloudwatch')

    # Get the list of RDS instances
    response = rds.describe_db_instances()
    for instance in response['DBInstances']:
        db_instance_id = instance['DBInstanceIdentifier']
        print(f"Checking instance {db_instance_id}")
        
        # Get the DatabaseConnections metric
        metric_statistics = cw.get_metric_statistics(
            Namespace='AWS/RDS',
            MetricName='DatabaseConnections',
            Dimensions=[
                {
                    'Name': 'DBInstanceIdentifier',
                    'Value': db_instance_id
                },
            ],
            StartTime=datetime.utcnow() - timedelta(hours=1),
            EndTime=datetime.utcnow(),
            Period=3600,  # hourly
            Statistics=['Sum', 'Average']
        )

        # Assume the instance is idle until we find a non-zero connection
        is_idle = True
        for datapoint in metric_statistics['Datapoints']:
            if datapoint['Sum'] > 0:
                is_idle = False
                break

        if is_idle:
            print(f"RDS instance {db_instance_id} has been idle for the past hour. Stopping the instance.")
            # Stop the instance
            rds.stop_db_instance(DBInstanceIdentifier=db_instance_id)
        else:
            print(f"RDS instance {db_instance_id} has active connections in the past hour.")

    return {
        'statusCode': 200,
        'body': 'Lambda function executed successfully!'
    }