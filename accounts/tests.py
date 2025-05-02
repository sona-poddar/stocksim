from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import UserProfile
from django.conf import settings

class UserProfileTests(TestCase):
    def setUp(self):
        self.test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
    
    def test_profile_creation(self):
        """Test that a profile is automatically created when a user is created"""
        self.assertTrue(hasattr(self.test_user, 'profile'))
        self.assertEqual(self.test_user.profile.balance, settings.INITIAL_BALANCE)
    
    def test_register_view(self):
        """Test the user registration view"""
        response = self.client.get(reverse('accounts:register'))
        self.assertEqual(response.status_code, 200)
        
        # Test registration with valid data
        response = self.client.post(reverse('accounts:register'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'complex_password123',
            'password2': 'complex_password123',
            'first_name': 'New',
            'last_name': 'User'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after successful registration
        self.assertTrue(User.objects.filter(username='newuser').exists())
    
    def test_profile_view(self):
        """Test the profile view"""
        self.client.login(username='testuser', password='testpassword123')
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'₹{settings.INITIAL_BALANCE:,.2f}')
