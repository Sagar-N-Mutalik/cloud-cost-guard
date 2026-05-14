import boto3
from datetime import datetime, timezone
from django.core.mail import send_mail
from .models import ScanResult

def run_scan_for_account(account):
    """Runs the scan logic for a single account and returns the number of zombies found."""
    sts_client = boto3.client('sts', region_name='us-east-1')
    zombies_found = 0
    
    try:
        # 1. Assume Role
        assumed_role = sts_client.assume_role(
            RoleArn=account.iam_role_arn,
            RoleSessionName="CostGuardWebScanner"
        )
        creds = assumed_role['Credentials']
        
        # 2. Fetch all AWS Regions
        temp_ec2 = boto3.client('ec2', aws_access_key_id=creds['AccessKeyId'], aws_secret_access_key=creds['SecretAccessKey'], aws_session_token=creds['SessionToken'], region_name='us-east-1')
        regions = [region['RegionName'] for region in temp_ec2.describe_regions()['Regions']]
        
        # Clear old results for this account so the dashboard only shows the *latest* state
        ScanResult.objects.filter(account=account).delete()
        
        email_message = f"Hello {account.user.username},\n\nWarning! We found active resources in your AWS account ({account.account_name}):\n\n"

        for region in regions:
            # Initialize regional client
            ec2 = boto3.client('ec2', aws_access_key_id=creds['AccessKeyId'], aws_secret_access_key=creds['SecretAccessKey'], aws_session_token=creds['SessionToken'], region_name=region)
            
            # 3. Scan EC2 Instances in region
            instances = ec2.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
            
            for reservation in instances['Reservations']:
                for instance in reservation['Instances']:
                    instance_id = instance['InstanceId']
                    uptime = datetime.now(timezone.utc) - instance['LaunchTime']
                    hours = uptime.total_seconds() / 3600
                    
                    # Save to DB
                    ScanResult.objects.create(account=account, instance_id=f"EC2 ({region}): {instance_id}", hours_running=hours)
                    email_message += f"- EC2 Instance ({region}): {instance_id} (Running for {round(hours, 1)} hours)\n"
                    zombies_found += 1

        # (You can copy your NAT and RDS checks here just like in the management command!)

        if zombies_found > 0:
            send_mail(
                subject='AWS Cost Alert - Running Resources Detected!',
                message=email_message,
                from_email=None,
                recipient_list=[account.user.email],
                fail_silently=True,
            )
            
    except Exception as e:
        print(f"Scan failed for {account.account_name}: {e}")
        return (-1, str(e)) # Indicates an error (like Access Denied)

    return (zombies_found, None)