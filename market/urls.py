from django.urls import path
from . import views

app_name = 'market'

urlpatterns = [
    path('', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('trade/', views.trade, name='trade'),
    path('stock/<str:symbol>/', views.stock_detail, name='stock_detail'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('challenges/', views.challenges, name='challenges'),
    path('challenges/<int:challenge_id>/', views.challenge_detail, name='challenge_detail'),
    path('api/search-stock/', views.search_stock_api, name='search_stock_api'),
]
