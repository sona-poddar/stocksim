from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Portfolio, StockHolding, Transaction, Challenge
from decimal import Decimal
from unittest.mock import patch
from django.utils import timezone
from datetime import timedelta

class MarketViewsTest(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        
        # Create a portfolio
        self.portfolio = Portfolio.objects.create(user=self.user)
        
        # Set up the client
        self.client = Client()
    
    @patch('market.utils.get_nifty50_stocks')
    def test_index_view(self, mock_get_nifty50):
        # Mock the return value of get_nifty50_stocks
        mock_get_nifty50.return_value = [
            {
                'symbol': 'RELIANCE.NS',
                'name': 'Reliance Industries Ltd',
                'current_price': 2500.0,
                'change_percent': 2.5
            },
            {
                'symbol': 'TCS.NS',
                'name': 'Tata Consultancy Services Ltd',
                'current_price': 3500.0,
                'change_percent': -1.2
            }
        ]
        
        response = self.client.get(reverse('market:index'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'market/index.html')
        self.assertIn('nifty50_data', response.context)
        self.assertIn('gainers', response.context)
        self.assertIn('losers', response.context)
    
    def test_dashboard_view_authentication(self):
        # Test that unauthenticated users are redirected
        response = self.client.get(reverse('market:dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Login and test again
        self.client.login(username='testuser', password='testpassword123')
        response = self.client.get(reverse('market:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'market/dashboard.html')
    
    @patch('market.utils.get_stock_info')
    def test_stock_detail_view(self, mock_get_stock_info):
        # Mock the return value of get_stock_info
        mock_get_stock_info.return_value = {
            'symbol': 'RELIANCE.NS',
            'name': 'Reliance Industries Ltd',
            'current_price': 2500.0,
            'change_percent': 2.5,
            'previous_close': 2450.0,
            'open': 2460.0,
            'day_high': 2520.0,
            'day_low': 2480.0,
            'volume': 5000000,
            'market_cap': 1600000000000,
            'pe_ratio': 30.5,
            'dividend_yield': 0.5,
            'fifty_two_week_high': 2600.0,
            'fifty_two_week_low': 1900.0
        }
        
        # Login
        self.client.login(username='testuser', password='testpassword123')
        
        # Test stock detail view
        response = self.client.get(reverse('market:stock_detail', args=['RELIANCE.NS']))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'market/stock_detail.html')
        self.assertIn('stock', response.context)
        self.assertEqual(response.context['stock']['symbol'], 'RELIANCE.NS')
    
    @patch('market.utils.get_nifty50_stocks')
    def test_trade_view_get(self, mock_get_nifty50):
        # Mock the return value
        mock_get_nifty50.return_value = [
            {'symbol': 'RELIANCE.NS', 'name': 'Reliance Industries Ltd', 'current_price': 2500.0},
            {'symbol': 'TCS.NS', 'name': 'Tata Consultancy Services Ltd', 'current_price': 3500.0}
        ]
        
        # Login
        self.client.login(username='testuser', password='testpassword123')
        
        # Test trade view
        response = self.client.get(reverse('market:trade'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'market/trade.html')
        self.assertIn('stocks', response.context)
    
    @patch('market.utils.get_stock_info')
    def test_buy_stock(self, mock_get_stock_info):
        # Mock the return value
        mock_get_stock_info.return_value = {
            'symbol': 'RELIANCE.NS',
            'name': 'Reliance Industries Ltd',
            'current_price': 2500.0
        }
        
        # Login
        self.client.login(username='testuser', password='testpassword123')
        
        # Initial balance should be 100000
        self.assertEqual(self.user.profile.balance, Decimal('100000.00'))
        
        # Buy 2 shares
        response = self.client.post(reverse('market:trade'), {
            'symbol': 'RELIANCE.NS',
            'quantity': 2,
            'transaction_type': 'buy'
        })
        
        # Should redirect to dashboard
        self.assertEqual(response.status_code, 302)
        
        # Check balance is updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.profile.balance, Decimal('100000.00') - (Decimal('2500.00') * 2))
        
        # Check holding is created
        holding = StockHolding.objects.get(portfolio=self.portfolio, stock_symbol='RELIANCE.NS')
        self.assertEqual(holding.quantity, 2)
        self.assertEqual(holding.average_buy_price, Decimal('2500.00'))
        
        # Check transaction is created
        transaction = Transaction.objects.get(portfolio=self.portfolio, stock_symbol='RELIANCE.NS')
        self.assertEqual(transaction.transaction_type, 'buy')
        self.assertEqual(transaction.quantity, 2)
        self.assertEqual(transaction.price, Decimal('2500.00'))

class ChallengeModelTest(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
    
    def test_challenge_status_updates(self):
        # Create a challenge that should start in the past and end in the future
        now = timezone.now()
        start_date = now - timedelta(days=1)
        end_date = now + timedelta(days=5)
        
        challenge = Challenge.objects.create(
            name='Test Challenge',
            description='Testing challenge status',
            creator=self.user,
            start_date=start_date,
            end_date=end_date
        )
        
        # Status should be ACTIVE since it has started but not ended
        self.assertEqual(challenge.status, Challenge.ACTIVE)
        
        # Create a completed challenge
        past_end = now - timedelta(days=1)
        past_start = now - timedelta(days=10)
        
        completed_challenge = Challenge.objects.create(
            name='Completed Challenge',
            description='Already finished',
            creator=self.user,
            start_date=past_start,
            end_date=past_end
        )
        
        # Status should be COMPLETED
        self.assertEqual(completed_challenge.status, Challenge.COMPLETED)
        
        # Create a future challenge
        future_start = now + timedelta(days=5)
        future_end = now + timedelta(days=15)
        
        future_challenge = Challenge.objects.create(
            name='Future Challenge',
            description='Not started yet',
            creator=self.user,
            start_date=future_start,
            end_date=future_end
        )
        
        # Status should be PENDING
        self.assertEqual(future_challenge.status, Challenge.PENDING)
