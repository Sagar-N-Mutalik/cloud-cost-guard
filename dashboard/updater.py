from apscheduler.schedulers.background import BackgroundScheduler
from django.core.management import call_command

def start_scanner():
    # This runs your 'scan_costs' command silently in the background
    call_command('scan_costs')

def start():
    scheduler = BackgroundScheduler()
    # Schedule it to run every 4 hours (For testing, you can change 'hours=4' to 'minutes=1')
    scheduler.add_job(start_scanner, 'interval', hours=4) # Change to hours=4 in production
    scheduler.start()