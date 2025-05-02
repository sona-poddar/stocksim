from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegisterForm, UserUpdateForm
from market.models import Portfolio, Transaction, StockHolding


@login_required
def profile(request):
    """Display and update user profile"""
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('accounts:profile')
    else:
        form = UserUpdateForm(instance=request.user)
    
    # Get user's portfolio and transactions
    try:
        portfolio = Portfolio.objects.get(user=request.user)
        holdings = StockHolding.objects.filter(portfolio=portfolio)
        transactions = Transaction.objects.filter(portfolio=portfolio).order_by('-timestamp')[:10]
    except Portfolio.DoesNotExist:
        portfolio = None
        holdings = []
        transactions = []
    
    context = {
        'form': form,
        'user_profile': request.user.profile,
        'portfolio': portfolio,
        'holdings': holdings,
        'transactions': transactions,
    }
    return render(request, 'accounts/profile.html', context)

def register(request):
    """Register a new user"""
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            
            # Create portfolio for the new user
            Portfolio.objects.create(user=user)
            
            return redirect('accounts:login')
    else:
        form = UserRegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


def logoutUser(request):
    logout(request)
    return redirect('market:index')