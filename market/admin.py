from django.contrib import admin
from .models import Portfolio, StockHolding, Transaction, Challenge, ChallengeParticipant

@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_value', 'created_at')
    search_fields = ('user__username',)

@admin.register(StockHolding)
class StockHoldingAdmin(admin.ModelAdmin):
    list_display = ('portfolio', 'stock_symbol', 'quantity', 'average_buy_price')
    list_filter = ('stock_symbol',)
    search_fields = ('portfolio__user__username', 'stock_symbol')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('portfolio', 'timestamp', 'stock_symbol', 'transaction_type', 'quantity', 'price')
    list_filter = ('transaction_type', 'stock_symbol')
    search_fields = ('portfolio__user__username', 'stock_symbol')
    date_hierarchy = 'timestamp'

@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ('name', 'creator', 'start_date', 'end_date', 'status')
    list_filter = ('status',)
    search_fields = ('name', 'creator__username')

@admin.register(ChallengeParticipant)
class ChallengeParticipantAdmin(admin.ModelAdmin):
    list_display = ('user', 'challenge', 'join_date', 'final_portfolio_value')
    list_filter = ('challenge',)
    search_fields = ('user__username', 'challenge__name')
