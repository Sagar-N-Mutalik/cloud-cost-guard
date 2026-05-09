from django.db import models
from django.contrib.auth.models import User

class ConnectedAccount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    account_name = models.CharField(max_length=100, help_text="e.g., Hackathon Account")
    iam_role_arn = models.CharField(max_length=255, help_text="The Role ARN the user created for us")
    created_at = models.DateTimeField(auto_now_add=True)
    last_scanned = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.account_name}"

class ScanResult(models.Model):
    account = models.ForeignKey(ConnectedAccount, on_delete=models.CASCADE)
    instance_id = models.CharField(max_length=100)
    hours_running = models.FloatField()
    scan_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.instance_id} ({self.hours_running} hrs)"