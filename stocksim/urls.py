"""
URL configuration for stocksim project.
"""

from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('', include('market.urls')),
    # Redirect root to market index
    path('', RedirectView.as_view(pattern_name='market:index')),
]
