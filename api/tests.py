from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import Profile
from nutrition.models import Dish, MealPlan
from nutrition.tests import make_dish


class RegisterViewIntegrationTests(TestCase):
    def test_register_page_renders(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create Your Account')

    def test_register_rejects_missing_human_check(self):
        response = self.client.post(reverse('register'), {
            'username': 'newbie',
            'email': 'newbie@example.com',
            'password1': 'strongpass123!',
            'password2': 'strongpass123!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'human verification')
        self.assertFalse(User.objects.filter(username='newbie').exists())

    def test_register_success_redirects_to_profile_setup(self):
        response = self.client.post(reverse('register'), {
            'username': 'newbie',
            'email': 'newbie@example.com',
            'password1': 'strongpass123!',
            'password2': 'strongpass123!',
            'human_check': 'verified',
        })
        self.assertRedirects(response, reverse('profile_setup'))
        self.assertTrue(User.objects.filter(username='newbie').exists())


class AuthIntegrationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='authuser', password='strongpass123!')

    def test_login_requires_no_extra_fields(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_login_and_logout_flow(self):
        ok = self.client.login(username='authuser', password='strongpass123!')
        self.assertTrue(ok)
        response = self.client.post(reverse('logout'))
        self.assertEqual(response.status_code, 302)


class ProtectedViewIntegrationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='protected', password='strongpass123!')

    def test_dashboard_redirects_anonymous_users(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_dashboard_redirects_to_profile_setup_without_profile(self):
        self.client.login(username='protected', password='strongpass123!')
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, reverse('profile_setup'))


class ProfileSetupIntegrationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='profileuser', password='strongpass123!')
        self.client.login(username='profileuser', password='strongpass123!')

    def test_profile_setup_creates_profile_and_redirects(self):
        response = self.client.post(reverse('profile_setup'), {
            'age': 30,
            'gender': 'male',
            'weight_kg': 80,
            'height_cm': 180,
            'goal': 'maintain',
            'swallow_preference': 'both',
            'spice_level': 'medium',
            'protein_preference': 'chicken',
            'cultural_region': 'general',
            'budget_level': 'moderate',
        })
        self.assertRedirects(response, reverse('dashboard'))
        self.assertTrue(Profile.objects.filter(user=self.user).exists())


class DashboardIntegrationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='dashuser', password='strongpass123!')
        Profile.objects.create(
            user=self.user, age=30, gender='male', weight_kg=80, height_cm=180, goal='maintain'
        )
        self.client.login(username='dashuser', password='strongpass123!')

    def test_dashboard_renders_analysis(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Your Nutrition Analysis')
        self.assertContains(response, 'Generate My Meal Plan')


class GeneratePlanIntegrationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='planuser', password='strongpass123!')
        self.profile = Profile.objects.create(
            user=self.user, age=30, gender='male', weight_kg=80, height_cm=180, goal='maintain'
        )
        for slot in ['breakfast', 'lunch', 'dinner', 'snack']:
            make_dish(f'Plan {slot.title()}', meal_type=slot)
        self.client.login(username='planuser', password='strongpass123!')

    def test_generate_plan_creates_meal_plan(self):
        response = self.client.post(reverse('generate_plan'))
        self.assertRedirects(response, reverse('dashboard'))
        plan = MealPlan.objects.filter(profile=self.profile).first()
        self.assertIsNotNone(plan)
        self.assertEqual(plan.entries.count(), 28)


class ShoppingListIntegrationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='shopuser', password='strongpass123!')
        self.profile = Profile.objects.create(
            user=self.user, age=30, gender='male', weight_kg=80, height_cm=180, goal='maintain'
        )
        self.client.login(username='shopuser', password='strongpass123!')

    def test_shopping_list_redirects_when_no_plan(self):
        response = self.client.get(reverse('shopping_list'))
        self.assertRedirects(response, reverse('dashboard'))

    def test_shopping_list_renders_with_plan(self):
        dish = make_dish('Shop Dish')
        plan = MealPlan.objects.create(
            profile=self.profile,
            daily_calorie_target=2000,
            daily_protein_target=100,
            daily_carb_target=200,
            daily_fat_target=60,
        )
        plan.entries.create(dish=dish, day_number=1, meal_type='lunch')
        response = self.client.get(reverse('shopping_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Your Shopping List')


class RateDishIntegrationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='rater', password='strongpass123!')
        self.client.login(username='rater', password='strongpass123!')
        self.dish = make_dish('Ratable Dish')

    def test_rate_dish_get_returns_405(self):
        response = self.client.get(reverse('rate_dish'))
        self.assertEqual(response.status_code, 405)

    def test_rate_dish_missing_data_returns_400(self):
        response = self.client.post(reverse('rate_dish'), {})
        self.assertEqual(response.status_code, 400)

    def test_rate_dish_invalid_stars_returns_400(self):
        response = self.client.post(reverse('rate_dish'), {'dish_id': self.dish.id, 'stars': '9'})
        self.assertEqual(response.status_code, 400)

    def test_rate_dish_success(self):
        response = self.client.post(reverse('rate_dish'), {'dish_id': self.dish.id, 'stars': '4'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'success': True, 'stars': 4})