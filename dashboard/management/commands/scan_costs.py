import boto3
from datetime import datetime, timezone
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from dashboard.models import ConnectedAccount, ScanResult

class Command(BaseCommand):
    help = 'Scans all connected AWS accounts for EC2 instances, NAT gateways, and RDS databases'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("Starting Comprehensive Cloud Cost Guard Scanner..."))
        sts_client = boto3.client('sts')
        accounts = ConnectedAccount.objects.all()

        if not accounts:
            self.stdout.write(self.style.WARNING("No accounts connected in the database yet."))
            return

        for account in accounts:
            self.stdout.write(f"Scanning account: {account.account_name}...")
            
            try:
                # 1. Securely assume the user's IAM Role
                assumed_role = sts_client.assume_role(
                    RoleArn=account.iam_role_arn,
                    RoleSessionName="CostGuardScanner"
                )
                creds = assumed_role['Credentials']
                
                # 2. Fetch all AWS Regions
                temp_ec2 = boto3.client(
                    'ec2',
                    aws_access_key_id=creds['AccessKeyId'],
                    aws_secret_access_key=creds['SecretAccessKey'],
                    aws_session_token=creds['SessionToken'],
                    region_name='us-east-1'
                )
                regions = [region['RegionName'] for region in temp_ec2.describe_regions()['Regions']]
                
                found_zombies = False
                email_message = f"Hello {account.user.username},\n\nWarning! We found these active resources running in your AWS account ({account.account_name}):\n\n"

                for region in regions:
                    try:
                        # Initialize regional clients
                        ec2 = boto3.client(
                            'ec2',
                            aws_access_key_id=creds['AccessKeyId'],
                            aws_secret_access_key=creds['SecretAccessKey'],
                            aws_session_token=creds['SessionToken'],
                            region_name=region
                        )

                        rds = boto3.client(
                            'rds',
                            aws_access_key_id=creds['AccessKeyId'],
                            aws_secret_access_key=creds['SecretAccessKey'],
                            aws_session_token=creds['SessionToken'],
                            region_name=region
                        )

                        # --- CHECK 1: EC2 INSTANCES ---
                        instances = ec2.describe_instances(
                            Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
                        )
                        for reservation in instances['Reservations']:
                            for instance in reservation['Instances']:
                                instance_id = instance['InstanceId']
                                uptime = datetime.now(timezone.utc) - instance['LaunchTime']
                                hours = uptime.total_seconds() / 3600
                                
                                ScanResult.objects.create(
                                    account=account,
                                    instance_id=f"EC2 ({region}): {instance_id}",
                                    hours_running=hours
                                )
                                
                                email_message += f"- EC2 Instance ({region}): {instance_id} (Running for {round(hours, 1)} hours)\n"
                                found_zombies = True

                        # --- CHECK 2: NAT GATEWAYS ---
                        nat_gateways = ec2.describe_nat_gateways(
                            Filters=[{'Name': 'state', 'Values': ['available']}]
                        )
                        for nat in nat_gateways['NatGateways']:
                            nat_id = nat['NatGatewayId']
                            uptime = datetime.now(timezone.utc) - nat['CreateTime']
                            hours = uptime.total_seconds() / 3600

                            ScanResult.objects.create(
                                account=account,
                                instance_id=f"NAT ({region}): {nat_id}",
                                hours_running=hours
                            )

                            email_message += f"- NAT Gateway ({region}): {nat_id} (Running for {round(hours, 1)} hours. High Cost Alert!)\n"
                            found_zombies = True

                        # --- CHECK 3: RDS DATABASES ---
                        databases = rds.describe_db_instances()
                        for db in databases['DBInstances']:
                            if db['DBInstanceStatus'] == 'available':
                                db_id = db['DBInstanceIdentifier']
                                uptime = datetime.now(timezone.utc) - db['InstanceCreateTime']
                                hours = uptime.total_seconds() / 3600

                                ScanResult.objects.create(
                                    account=account,
                                    instance_id=f"RDS ({region}): {db_id}",
                                    hours_running=hours
                                )

                                email_message += f"- RDS Database ({region}): {db_id} (Running for {round(hours, 1)} hours)\n"
                                found_zombies = True
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"Skipping region {region} due to error: {e}"))
                
                # --- FINAL STEP: SEND NOTIFICATION ---
                if found_zombies:
                    email_message += "\nPlease log into your AWS console and terminate them if they are no longer needed to prevent unexpected charges.\n\n- Cloud Cost Guard"
                    
                    send_mail(
                        subject=f'AWS Cost Alert - Running Resources Detected!',
                        message=email_message,
                        from_email=None, # Uses default from settings
                        recipient_list=[account.user.email],
                        fail_silently=False,
                    )
                    self.stdout.write(self.style.ERROR(f"Found running resources for {account.account_name}. Alert email sent!"))
                else:
                    self.stdout.write(self.style.SUCCESS(f"Clean! No running resources found for {account.account_name}."))

            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Failed scanning {account.account_name}. Error: {str(e)}"))