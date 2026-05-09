from django.contrib import admin
from .models import ConnectedAccount, ScanResult

admin.site.register(ConnectedAccount)
admin.site.register(ScanResult)