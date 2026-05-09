from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth import login
from .models import ConnectedAccount, ScanResult
from .scanner import run_scan_for_account

@login_required(login_url='/accounts/login/') 
def dashboard_view(request):
    # Handle the form submission to add a new AWS Account ARN
    if request.method == 'POST':
        account_name = request.POST.get('account_name')
        role_arn = request.POST.get('role_arn')
        
        if account_name and role_arn:
            # Save the account
            account = ConnectedAccount.objects.create(
                user=request.user,
                account_name=account_name,
                iam_role_arn=role_arn
            )
            
            # TRIGGER LIVE SCAN IMMEDIATELY
            status = run_scan_for_account(account)
            
            # Send flash messages to the UI based on the scan result
            if status == -1:
                messages.error(request, "Account saved, but we couldn't scan it. Please check your IAM Role ARN permissions.")
            elif status > 0:
                messages.warning(request, f"Account connected! Warning: We immediately found {status} running resources. An email has been sent. Next background scan in 4 hours.")
            else:
                messages.success(request, "Account connected! Initial scan complete (0 running resources found). Next background scan in 4 hours.")
                
            return redirect('dashboard') # Refresh the page after saving

    # Get the user's connected accounts and any recent scan alerts from the database
    accounts = ConnectedAccount.objects.filter(user=request.user)
    recent_alerts = ScanResult.objects.filter(account__in=accounts).order_by('-scan_time')[:10]

    context = {
        'accounts': accounts,
        'recent_alerts': recent_alerts
    }
    return render(request, 'dashboard.html', context)

def register(request):
    """Handles new user sign-ups"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user) # Automatically log them in after signup
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    
    return render(request, 'register.html', {'form': form})

@login_required(login_url='/accounts/login/')
def delete_account(request, account_id):
    """Ensures the user can only delete an account that belongs to them"""
    account = get_object_or_404(ConnectedAccount, id=account_id, user=request.user)
    
    if request.method == 'POST':
        account_name = account.account_name
        account.delete()
        messages.success(request, f"Account '{account_name}' has been successfully deleted. We have stopped monitoring it.")
        
    return redirect('dashboard')

@login_required(login_url='/accounts/login/')
def manual_scan(request, account_id):
    """Triggered when the user clicks the 'Scan Now' button"""
    account = get_object_or_404(ConnectedAccount, id=account_id, user=request.user)
    
    status = run_scan_for_account(account)
    
    if status == -1:
        messages.error(request, f"Scan failed for {account.account_name}. Ensure your AWS IAM Role has the 'ViewOnlyAccess' permission attached.")
    elif status > 0:
        messages.warning(request, f"Scan complete! We found {status} running resources in {account.account_name}.")
    else:
        messages.success(request, f"Scan complete! {account.account_name} is perfectly clean.")
        
    return redirect('dashboard')