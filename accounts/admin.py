from django.contrib import admin
from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'date_joined')
    search_fields = ('user__username', 'user__email')
    list_filter = ('date_joined',)
