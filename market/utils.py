import os
import requests
import json
from datetime import datetime, timedelta
from decimal import Decimal
import random
import logging
from django.utils import timezone
from django.conf import settings

logger = logging.getLogger(__name__)

# Define Nifty 50 stocks (as a fallback if API calls fail)
NIFTY50_STOCKS = [
    {"symbol": "RELIANCE.NS", "name": "Reliance Industries Ltd"},
    {"symbol": "TCS.NS", "name": "Tata Consultancy Services Ltd"},
    {"symbol": "HDFCBANK.NS", "name": "HDFC Bank Ltd"},
    {"symbol": "INFY.NS", "name": "Infosys Ltd"},
    {"symbol": "ICICIBANK.NS", "name": "ICICI Bank Ltd"},
    {"symbol": "HINDUNILVR.NS", "name": "Hindustan Unilever Ltd"},
    {"symbol": "HDFC.NS", "name": "Housing Development Finance Corporation Ltd"},
    {"symbol": "SBIN.NS", "name": "State Bank of India"},
    {"symbol": "BHARTIARTL.NS", "name": "Bharti Airtel Ltd"},
    {"symbol": "KOTAKBANK.NS", "name": "Kotak Mahindra Bank Ltd"},
    {"symbol": "ITC.NS", "name": "ITC Ltd"},
    {"symbol": "LT.NS", "name": "Larsen & Toubro Ltd"},
    {"symbol": "ASIANPAINT.NS", "name": "Asian Paints Ltd"},
    {"symbol": "AXISBANK.NS", "name": "Axis Bank Ltd"},
    {"symbol": "BAJFINANCE.NS", "name": "Bajaj Finance Ltd"}
]

def get_yahoo_finance_url(endpoint, params=None):
    """Construct and return Yahoo Finance API URL"""
    base_url = "https://query1.finance.yahoo.com/v8/finance"
    url = f"{base_url}/{endpoint}"
    
    if params:
        param_string = "&".join([f"{k}={v}" for k, v in params.items()])
        url = f"{url}?{param_string}"
    
    return url

def get_stock_info(symbol):
    """Get detailed information about a stock"""
    try:
        # If the symbol doesn't have a suffix, add .NS for Indian stocks
        if "." not in symbol:
            symbol = f"{symbol}.NS"
        
        # Check if we're in a fallback situation (for rate limiting)
        # In a real app, we'd check a Redis cache or similar
        global _use_fallback
        if globals().get('_use_fallback', False):
            # Return fallback data directly instead of making API calls
            return get_fallback_stock_info(symbol)
            
        url = get_yahoo_finance_url("quote", {"symbols": symbol})
        response = requests.get(url, timeout=5)
        
        if response.status_code == 429:  # Rate limit exceeded
            logger.warning(f"Rate limit exceeded for Yahoo Finance API. Using fallback data.")
            # Set global flag to avoid more API calls in this session
            globals()['_use_fallback'] = True
            return get_fallback_stock_info(symbol)
        
        if response.status_code != 200:
            logger.error(f"Failed to get stock info for {symbol}: {response.status_code}")
            return get_fallback_stock_info(symbol)
        
        data = response.json()
        
        try:
            quote_data = data['quoteResponse']['result'][0]
            
            return {
                'symbol': quote_data.get('symbol', symbol),
                'name': quote_data.get('longName', quote_data.get('shortName', symbol)),
                'current_price': quote_data.get('regularMarketPrice', 0),
                'change': quote_data.get('regularMarketChange', 0),
                'change_percent': quote_data.get('regularMarketChangePercent', 0),
                'previous_close': quote_data.get('regularMarketPreviousClose', 0),
                'open': quote_data.get('regularMarketOpen', 0),
                'day_high': quote_data.get('regularMarketDayHigh', 0),
                'day_low': quote_data.get('regularMarketDayLow', 0),
                'volume': quote_data.get('regularMarketVolume', 0),
                'market_cap': quote_data.get('marketCap', 0),
                'pe_ratio': quote_data.get('trailingPE', 0),
                'dividend_yield': quote_data.get('dividendYield', 0) if 'dividendYield' in quote_data else 0,
                'fifty_two_week_high': quote_data.get('fiftyTwoWeekHigh', 0),
                'fifty_two_week_low': quote_data.get('fiftyTwoWeekLow', 0)
            }
        except (KeyError, IndexError) as e:
            logger.error(f"Error parsing Yahoo Finance data for {symbol}: {e}")
            return get_fallback_stock_info(symbol)
    
    except Exception as e:
        logger.error(f"Error fetching stock data for {symbol}: {e}")
        return get_fallback_stock_info(symbol)

def get_fallback_stock_info(symbol):
    """Generate fallback data for a stock when API is unavailable"""
    # Find stock in NIFTY50_STOCKS if possible
    stock_name = symbol
    for stock in NIFTY50_STOCKS:
        if stock['symbol'] == symbol:
            stock_name = stock['name']
            break

    # Seed random with symbol to get consistent results for same symbol
    random.seed(hash(symbol) + int(datetime.now().timestamp()) // 3600)
    
    # Create random but realistic looking stock data
    base_price = random.uniform(500, 5000)
    change_percent = random.uniform(-5, 5)
    change = base_price * change_percent / 100
    prev_close = base_price - change
    
    return {
        'symbol': symbol,
        'name': stock_name,
        'current_price': base_price,
        'change': change,
        'change_percent': change_percent,
        'previous_close': prev_close,
        'open': prev_close * (1 + random.uniform(-1, 1) / 100),
        'day_high': base_price * (1 + random.uniform(0, 2) / 100),
        'day_low': base_price * (1 - random.uniform(0, 2) / 100),
        'volume': random.randint(100000, 10000000),
        'market_cap': base_price * random.randint(10000000, 1000000000),
        'pe_ratio': random.uniform(5, 50),
        'dividend_yield': random.uniform(0, 5),
        'fifty_two_week_high': base_price * (1 + random.uniform(5, 25) / 100),
        'fifty_two_week_low': base_price * (1 - random.uniform(5, 25) / 100)
    }

def get_current_stock_price(symbol):
    """Get current stock price only"""
    try:
        stock_info = get_stock_info(symbol)
        if stock_info:
            return Decimal(str(stock_info['current_price']))
        return Decimal('0.0')
    except Exception as e:
        logger.error(f"Error getting current price for {symbol}: {e}")
        return Decimal('0.0')

def search_stocks(query):
    """Search for stocks based on query"""
    try:
        # If we're in fallback mode, return filtered fallback stocks
        if globals().get('_use_fallback', False):
            return search_fallback_stocks(query)
            
        # Construct URL for Yahoo Finance search API
        url = f"https://query1.finance.yahoo.com/v1/finance/search?q={query}&quotesCount=10&newsCount=0&enableFuzzyQuery=false&region=IN"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 429:  # Rate limit exceeded
            logger.warning(f"Rate limit exceeded when searching stocks. Using fallback data.")
            globals()['_use_fallback'] = True
            return search_fallback_stocks(query)
            
        if response.status_code != 200:
            logger.error(f"Failed to search stocks for {query}: {response.status_code}")
            return search_fallback_stocks(query)
        
        data = response.json()
        
        results = []
        for quote in data.get('quotes', []):
            if 'symbol' in quote and 'NS' in quote['symbol']:  # Only include NSE stocks
                stock_info = {
                    'symbol': quote.get('symbol', ''),
                    'name': quote.get('longname', quote.get('shortname', '')),
                    'exchange': quote.get('exchange', '')
                }
                
                # Get current price and other details
                detailed_info = get_stock_info(stock_info['symbol'])
                if detailed_info:
                    stock_info.update({
                        'current_price': detailed_info['current_price'],
                        'change_percent': detailed_info['change_percent']
                    })
                
                results.append(stock_info)
        
        if results:
            return results
        else:
            return search_fallback_stocks(query)
    
    except Exception as e:
        logger.error(f"Error searching stocks for {query}: {e}")
        return search_fallback_stocks(query)

def search_fallback_stocks(query):
    """Search fallback stocks based on query"""
    query = query.lower()
    results = []
    
    # Generate fallback data for all stocks in NIFTY50_STOCKS
    all_stocks = get_fallback_nifty50_data()
    
    # Filter based on query
    for stock in all_stocks:
        if (query in stock['symbol'].lower() or 
            query in stock['name'].lower()):
            results.append(stock)
    
    # Return top 10 matches
    return results[:10]

def get_nifty50_stocks():
    """Get Nifty 50 stocks data"""
    try:
        nifty50_data = []
        
        # Try to get data for predefined Nifty 50 stocks
        for stock in NIFTY50_STOCKS:
            stock_info = get_stock_info(stock['symbol'])
            if stock_info:
                nifty50_data.append(stock_info)
        
        # If we got any real data, return it
        if nifty50_data:
            return nifty50_data
        
        # Otherwise, use fallback data
        logger.warning("Using fallback data for Nifty 50 stocks due to API limitations")
        return get_fallback_nifty50_data()
    
    except Exception as e:
        logger.error(f"Error fetching Nifty 50 stocks: {e}")
        return get_fallback_nifty50_data()

def get_fallback_nifty50_data():
    """Generate fallback data for Nifty 50 stocks"""
    # Seed the random generator for consistent results in a session
    random.seed(int(datetime.now().timestamp()) // 3600)  # Change hourly
    
    # Create realistic fallback data
    return [
        {
            'symbol': stock['symbol'],
            'name': stock['name'],
            'current_price': random.uniform(500, 5000),
            'change_percent': random.uniform(-5, 5),
            'previous_close': random.uniform(500, 5000),
            'open': random.uniform(500, 5000),
            'day_high': random.uniform(500, 5000),
            'day_low': random.uniform(500, 5000),
            'volume': random.randint(100000, 10000000),
            'market_cap': random.randint(1000000000, 10000000000000),
            'pe_ratio': random.uniform(5, 50),
            'dividend_yield': random.uniform(0, 5),
            'fifty_two_week_high': random.uniform(500, 5000),
            'fifty_two_week_low': random.uniform(500, 5000)
        }
        for stock in NIFTY50_STOCKS
    ]

def calculate_portfolio_history(portfolio):
    """
    Calculate portfolio value history for charts
    For demo purposes, this generates simulated historical data
    In a real application, this would use stored historical transaction data
    """
    try:
        # Get all transactions sorted by time
        from .models import Transaction
        transactions = Transaction.objects.filter(portfolio=portfolio).order_by('timestamp')
        
        if not transactions:
            return []
        
        # Start date is 30 days ago or first transaction, whichever is more recent
        start_date = max(
            transactions.first().timestamp.date(),
            timezone.now().date() - timedelta(days=30)
        )
        
        # End date is today
        end_date = timezone.now().date()
        
        # Generate daily data points
        history = []
        current_date = start_date
        
        # For simplicity, we're simulating historical data
        # In a real application, you would calculate each day's value based on 
        # transaction history and historical stock prices
        
        # Get current portfolio value
        current_value = portfolio.net_worth
        
        # Generate a somewhat realistic growth curve going backward from current value
        while current_date <= end_date:
            # Calculate a modifier for this day (random variation around a trend)
            days_ago = (end_date - current_date).days
            
            if days_ago > 0:
                # Simulate a general upward or downward trend with random variations
                # This is simplified and would be replaced with actual calculations
                trend_factor = 1 - (days_ago * 0.005)  # Gradual trend
                random_factor = 1 + (random.uniform(-0.02, 0.02))  # Daily noise
                value = current_value * trend_factor * random_factor
            else:
                value = current_value
            
            history.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'value': round(value, 2)
            })
            
            current_date += timedelta(days=1)
        
        return history
    
    except Exception as e:
        logger.error(f"Error calculating portfolio history: {e}")
        return []
