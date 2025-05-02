from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.db.models import F, Sum, Q
from django.db import transaction
from decimal import Decimal

from .models import Portfolio, StockHolding, Transaction, Challenge, ChallengeParticipant
from .utils import (
    get_stock_info, get_current_stock_price, search_stocks,
    get_nifty50_stocks, calculate_portfolio_history
)

def index(request):
    """Home page view"""
    nifty50_data = get_nifty50_stocks()
    
    # Get top gainers and losers from Nifty 50
    gainers = sorted(nifty50_data, key=lambda x: x['change_percent'], reverse=True)[:5]
    losers = sorted(nifty50_data, key=lambda x: x['change_percent'])[:5]
    
    context = {
        'nifty50_data': nifty50_data[:10],  # Show top 10 stocks
        'gainers': gainers,
        'losers': losers
    }
    return render(request, 'market/index.html', context)

@login_required
def dashboard(request):
    """User dashboard view"""
    try:
        portfolio = Portfolio.objects.get(user=request.user)
        holdings = StockHolding.objects.filter(portfolio=portfolio)
        
        # Get portfolio history for charts
        portfolio_history = calculate_portfolio_history(portfolio)
        
        # Get latest transactions
        transactions = Transaction.objects.filter(portfolio=portfolio).order_by('-timestamp')[:5]
        
    except Portfolio.DoesNotExist:
        # Create portfolio if it doesn't exist
        portfolio = Portfolio.objects.create(user=request.user)
        holdings = []
        portfolio_history = []
        transactions = []
    
    context = {
        'portfolio': portfolio,
        'holdings': holdings,
        'portfolio_history': portfolio_history,
        'transactions': transactions,
        'balance': request.user.profile.balance,
        'net_worth': portfolio.net_worth
    }
    return render(request, 'market/dashboard.html', context)

@login_required
def stock_detail(request, symbol):
    """View details of a specific stock"""
    stock_info = get_stock_info(symbol)
    
    if not stock_info:
        messages.error(request, "Could not retrieve stock information. Please try again later.")
        return redirect('market:dashboard')
    
    # Check if user owns this stock
    try:
        portfolio = Portfolio.objects.get(user=request.user)
        try:
            holding = StockHolding.objects.get(portfolio=portfolio, stock_symbol=symbol)
        except StockHolding.DoesNotExist:
            holding = None
    except Portfolio.DoesNotExist:
        portfolio = None
        holding = None
    
    context = {
        'stock': stock_info,
        'holding': holding,
        'balance': request.user.profile.balance
    }
    return render(request, 'market/stock_detail.html', context)

@login_required
def trade(request):
    """View for trading stocks"""
    if request.method == 'POST':
        symbol = request.POST.get('symbol')
        quantity = int(request.POST.get('quantity', 0))
        transaction_type = request.POST.get('transaction_type')
        
        if quantity <= 0:
            messages.error(request, "Quantity must be greater than zero.")
            return redirect('market:trade')
        
        # Get stock info and validate
        stock_info = get_stock_info(symbol)
        if not stock_info:
            messages.error(request, "Invalid stock symbol or could not retrieve stock information.")
            return redirect('market:trade')
        
        current_price = Decimal(str(stock_info['current_price']))
        total_amount = current_price * quantity
        
        # Get or create portfolio
        portfolio, created = Portfolio.objects.get_or_create(user=request.user)
        
        # Execute transaction based on type
        with transaction.atomic():
            if transaction_type == Transaction.BUY:
                # Check if user has enough balance
                if request.user.profile.balance < total_amount:
                    messages.error(request, f"Insufficient funds. You need ₹{total_amount} but have ₹{request.user.profile.balance}.")
                    return redirect('market:trade')
                
                # Update user balance
                request.user.profile.balance -= total_amount
                request.user.profile.save()
                
                # Update or create holding
                holding, created = StockHolding.objects.get_or_create(
                    portfolio=portfolio,
                    stock_symbol=symbol,
                    defaults={
                        'stock_name': stock_info['name'],
                        'quantity': 0,
                        'average_buy_price': 0
                    }
                )
                
                # Update average buy price
                total_value = (holding.quantity * holding.average_buy_price) + total_amount
                holding.quantity += quantity
                holding.average_buy_price = total_value / holding.quantity if holding.quantity > 0 else 0
                holding.save()
                
                # Create transaction record
                Transaction.objects.create(
                    portfolio=portfolio,
                    stock_symbol=symbol,
                    stock_name=stock_info['name'],
                    transaction_type=Transaction.BUY,
                    quantity=quantity,
                    price=current_price
                )
                
                messages.success(request, f"Successfully bought {quantity} shares of {symbol} at ₹{current_price} per share.")
                
            elif transaction_type == Transaction.SELL:
                # Check if user has the stock and enough quantity
                try:
                    holding = StockHolding.objects.get(portfolio=portfolio, stock_symbol=symbol)
                    if holding.quantity < quantity:
                        messages.error(request, f"You only have {holding.quantity} shares of {symbol} but are trying to sell {quantity}.")
                        return redirect('market:trade')
                except StockHolding.DoesNotExist:
                    messages.error(request, f"You don't own any shares of {symbol}.")
                    return redirect('market:trade')
                
                # Update user balance
                request.user.profile.balance += total_amount
                request.user.profile.save()
                
                # Update holding
                holding.quantity -= quantity
                if holding.quantity == 0:
                    holding.delete()
                else:
                    holding.save()
                
                # Create transaction record
                Transaction.objects.create(
                    portfolio=portfolio,
                    stock_symbol=symbol,
                    stock_name=stock_info['name'],
                    transaction_type=Transaction.SELL,
                    quantity=quantity,
                    price=current_price
                )
                
                messages.success(request, f"Successfully sold {quantity} shares of {symbol} at ₹{current_price} per share.")
        
        return redirect('market:dashboard')
    
    # For GET requests, show the trade page with search functionality
    query = request.GET.get('q', '')
    stocks = []
    
    if query:
        stocks = search_stocks(query)
    else:
        # Show Nifty 50 stocks by default
        stocks = get_nifty50_stocks()
    
    context = {
        'stocks': stocks,
        'query': query,
        'balance': request.user.profile.balance
    }
    return render(request, 'market/trade.html', context)

@login_required
def search_stock_api(request):
    """API endpoint for searching stocks"""
    query = request.GET.get('q', '')
    if not query:
        return JsonResponse({'results': []})
    
    results = search_stocks(query)
    return JsonResponse({'results': results})

@login_required
def leaderboard(request):
    """View leaderboard of all users"""
    # Get all users with portfolios and calculate net worth
    users_data = []
    
    for portfolio in Portfolio.objects.all():
        users_data.append({
            'username': portfolio.user.username,
            'net_worth': portfolio.net_worth,
            'portfolio_value': portfolio.total_value,
            'cash_balance': portfolio.user.profile.balance
        })
    
    # Sort by net worth (highest first)
    users_data = sorted(users_data, key=lambda x: x['net_worth'], reverse=True)
    
    # Add ranking
    for i, user in enumerate(users_data):
        user['rank'] = i + 1
    
    context = {
        'users': users_data,
        'user_rank': next((user['rank'] for user in users_data if user['username'] == request.user.username), None)
    }
    return render(request, 'market/leaderboard.html', context)

@login_required
def challenges(request):
    """View available challenges"""
    if request.method == 'POST':
        # Create a new challenge
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        initial_balance = request.POST.get('initial_balance', 100000)
        
        # Validate input
        if not all([name, start_date, end_date]):
            messages.error(request, "Please fill all required fields.")
            return redirect('market:challenges')
        
        try:
            challenge = Challenge.objects.create(
                name=name,
                description=description,
                creator=request.user,
                start_date=start_date,
                end_date=end_date,
                initial_balance=initial_balance
            )
            
            # Creator automatically joins their own challenge
            ChallengeParticipant.objects.create(
                user=request.user,
                challenge=challenge
            )
            
            messages.success(request, f"Challenge '{name}' created successfully!")
        except Exception as e:
            messages.error(request, f"Error creating challenge: {str(e)}")
        
        return redirect('market:challenges')
    
    # Get all challenges
    active_challenges = Challenge.objects.filter(status=Challenge.ACTIVE)
    pending_challenges = Challenge.objects.filter(status=Challenge.PENDING)
    completed_challenges = Challenge.objects.filter(status=Challenge.COMPLETED)
    
    # Get user's participated challenges
    user_challenges = ChallengeParticipant.objects.filter(user=request.user).values_list('challenge_id', flat=True)
    
    context = {
        'active_challenges': active_challenges,
        'pending_challenges': pending_challenges,
        'completed_challenges': completed_challenges,
        'user_challenges': user_challenges
    }
    return render(request, 'market/challenges.html', context)

@login_required
def challenge_detail(request, challenge_id):
    """View details of a specific challenge"""
    challenge = get_object_or_404(Challenge, id=challenge_id)
    
    # Check if user is participating
    try:
        participant = ChallengeParticipant.objects.get(user=request.user, challenge=challenge)
        is_participant = True
    except ChallengeParticipant.DoesNotExist:
        participant = None
        is_participant = False
    
    # Handle join challenge request
    if request.method == 'POST' and 'join' in request.POST:
        if not is_participant:
            ChallengeParticipant.objects.create(
                user=request.user,
                challenge=challenge
            )
            messages.success(request, f"You have joined the challenge '{challenge.name}'!")
            return redirect('market:challenge_detail', challenge_id=challenge.id)
    
    # Get all participants with their rankings
    participants = ChallengeParticipant.objects.filter(challenge=challenge)
    
    participants_data = []
    for p in participants:
        # For completed challenges, use the stored final value
        if challenge.status == Challenge.COMPLETED and p.final_portfolio_value:
            portfolio_value = p.final_portfolio_value
        else:
            # For active challenges, calculate the current portfolio value
            try:
                portfolio = Portfolio.objects.get(user=p.user)
                portfolio_value = portfolio.net_worth
            except Portfolio.DoesNotExist:
                portfolio_value = challenge.initial_balance
        
        participants_data.append({
            'username': p.user.username,
            'join_date': p.join_date,
            'portfolio_value': portfolio_value
        })
    
    # Sort by portfolio value
    participants_data = sorted(participants_data, key=lambda x: x['portfolio_value'], reverse=True)
    
    # Add ranking
    for i, p in enumerate(participants_data):
        p['rank'] = i + 1
    
    context = {
        'challenge': challenge,
        'is_participant': is_participant,
        'participants': participants_data,
        'user_rank': next((p['rank'] for p in participants_data if p['username'] == request.user.username), None)
    }
    return render(request, 'market/challenge_detail.html', context)
