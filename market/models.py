from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from .utils import get_current_stock_price

class Portfolio(models.Model):
    """Model representing a user's portfolio"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='portfolio')
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Portfolio"
    
    @property
    def total_value(self):
        """Calculate the total value of all stock holdings"""
        holdings = self.holdings.all()
        total = sum(holding.current_value for holding in holdings)
        return total
    
    @property
    def total_profit(self):
        """Calculate the total profit/loss from all holdings"""
        holdings = self.holdings.all()
        total = sum(holding.profit_loss for holding in holdings)
        return total
    
    @property
    def net_worth(self):
        """Calculate user's net worth (portfolio value + cash balance)"""
        return self.total_value + self.user.profile.balance

class StockHolding(models.Model):
    """Model representing stocks held in a portfolio"""
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='holdings')
    stock_symbol = models.CharField(max_length=20)
    stock_name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=0)
    average_buy_price = models.DecimalField(max_digits=15, decimal_places=2)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('portfolio', 'stock_symbol')
    
    def __str__(self):
        return f"{self.portfolio.user.username}'s holding of {self.stock_symbol}"
    
    @property
    def current_price(self):
        """Get current price of the stock from Yahoo Finance API"""
        return get_current_stock_price(self.stock_symbol)
    
    @property
    def current_value(self):
        """Calculate current value of the holding"""
        return self.quantity * self.current_price
    
    @property
    def invested_value(self):
        """Calculate the invested value"""
        return self.quantity * self.average_buy_price
    
    @property
    def profit_loss(self):
        """Calculate profit/loss for this holding"""
        return self.current_value - self.invested_value
    
    @property
    def profit_loss_percentage(self):
        """Calculate profit/loss percentage"""
        if self.invested_value > 0:
            return (self.profit_loss / self.invested_value) * 100
        return 0

class Transaction(models.Model):
    """Model representing a buy/sell transaction"""
    BUY = 'buy'
    SELL = 'sell'
    TRANSACTION_TYPES = [
        (BUY, 'Buy'),
        (SELL, 'Sell'),
    ]
    
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='transactions')
    stock_symbol = models.CharField(max_length=20)
    stock_name = models.CharField(max_length=255)
    transaction_type = models.CharField(max_length=4, choices=TRANSACTION_TYPES)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=15, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.transaction_type} {self.quantity} {self.stock_symbol} at ₹{self.price}"
    
    @property
    def total_amount(self):
        """Calculate the total transaction amount"""
        return self.quantity * self.price

class Challenge(models.Model):
    """Model representing an investment challenge"""
    PENDING = 'pending'
    ACTIVE = 'active'
    COMPLETED = 'completed'
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (ACTIVE, 'Active'),
        (COMPLETED, 'Completed'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_challenges')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    initial_balance = models.DecimalField(max_digits=15, decimal_places=2, default=100000.00)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Update status based on dates when saving"""
        now = timezone.now()
        if now >= self.start_date and now < self.end_date:
            self.status = self.ACTIVE
        elif now >= self.end_date:
            self.status = self.COMPLETED
        super().save(*args, **kwargs)
    
    @property
    def participants_count(self):
        """Get the number of participants in the challenge"""
        return self.participants.count()
    
    @property
    def duration_days(self):
        """Calculate the duration of the challenge in days"""
        delta = self.end_date - self.start_date
        return delta.days

class ChallengeParticipant(models.Model):
    """Model representing a participant in a challenge"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='challenge_participations')
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name='participants')
    join_date = models.DateTimeField(auto_now_add=True)
    final_portfolio_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    class Meta:
        unique_together = ('user', 'challenge')
    
    def __str__(self):
        return f"{self.user.username} in {self.challenge.name}"
    
    @property
    def current_rank(self):
        """Calculate current rank in the challenge"""
        if self.challenge.status == Challenge.COMPLETED and self.final_portfolio_value is not None:
            better_performers = ChallengeParticipant.objects.filter(
                challenge=self.challenge,
                final_portfolio_value__gt=self.final_portfolio_value
            ).count()
            return better_performers + 1
        return None
