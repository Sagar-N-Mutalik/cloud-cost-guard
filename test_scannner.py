import boto3

# Connect to AWS EC2
ec2 = boto3.client('ec2', region_name='us-east-1') # change region if needed

print("Scanning for running instances...")

# Get all running instances
response = ec2.describe_instances(
    Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
)

found = False
for reservation in response['Reservations']:
    for instance in reservation['Instances']:
        print(f"Found Running Instance ID: {instance['InstanceId']}")
        print(f"Launched at: {instance['LaunchTime']}")
        found = True

if not found:
    print("No running instances found! You are saving money.")