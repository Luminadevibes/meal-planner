from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import Profile
from nutrition.models import MealPlan, Rating, Dish
from nutrition.tests import make_dish


class EndToEndRegistrationToDashboardTest(TestCase):
    """Full user journey: register -> set up profile -> dashboard analysis."""

    def test_complete_registration_to_dashboard_flow(self):
        response = self.client.post(reverse('register'), {
            'username': 'e2euser',
            'email': 'e2e@example.com',
            'password1': 'strongpass123!',
            'password2': 'strongpass123!',
            'human_check': 'verified',
        })
        self.assertRedirects(response, reverse('profile_setup'))

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

        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Your Nutrition Analysis')

        profile = Profile.objects.get(user__username='e2euser')
        self.assertEqual(profile.goal, 'maintain')


class EndToEndMealPlanJourneyTest(TestCase):
    """Full user journey: profile -> generate plan -> shopping list -> rate a dish."""

    def setUp(self):
        self.user = User.objects.create_user(username='e2eplanner', password='strongpass123!')
        self.profile = Profile.objects.create(
            user=self.user, age=30, gender='male', weight_kg=80, height_cm=180, goal='maintain'
        )
        for slot in ['breakfast', 'lunch', 'dinner', 'snack']:
            make_dish(f'E2E {slot.title()} A', meal_type=slot)
            make_dish(f'E2E {slot.title()} B', meal_type=slot)
        self.client.login(username='e2eplanner', password='strongpass123!')

    def test_full_plan_shopping_list_and_rating_journey(self):
        self.client.post(reverse('generate_plan'))
        plan = MealPlan.objects.get(profile=self.profile)
        self.assertEqual(plan.entries.count(), 28)

        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, 'Your 7-Day Meal Plan')
        self.assertContains(response, 'View Shopping List')

        response = self.client.get(reverse('shopping_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Your Shopping List')

        dish = plan.entries.first().dish
        response = self.client.post(reverse('rate_dish'), {'dish_id': dish.id, 'stars': '5'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['success'], True)

        rating = Rating.objects.get(user=self.user, dish=dish)
        self.assertEqual(rating.stars, 5)
        self.assertEqual(dish.average_rating(), 5.0)


class EndToEndPersistenceAcrossLoginTest(TestCase):
    """User's generated plan and ratings persist across a login/logout cycle."""

    def setUp(self):
        self.user = User.objects.create_user(username='e2epersist', password='strongpass123!')
        self.profile = Profile.objects.create(
            user=self.user, age=30, gender='male', weight_kg=80, height_cm=180, goal='maintain'
        )
        dish = make_dish('Persistent Dish', meal_type='dinner')
        self.plan = MealPlan.objects.create(
            profile=self.profile,
            daily_calorie_target=2000,
            daily_protein_target=100,
            daily_carb_target=200,
            daily_fat_target=60,
        )
        self.plan.entries.create(dish=dish, day_number=1, meal_type='dinner')
        Rating.objects.create(user=self.user, dish=dish, stars=4)

    def test_plan_and_rating_survive_logout_login(self):
        self.client.logout()
        self.client.login(username='e2epersist', password='strongpass123!')

        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Your 7-Day Meal Plan')

        plan = MealPlan.objects.get(profile=self.profile)
        self.assertEqual(plan.entries.count(), 1)

        dish = Dish.objects.get(name='Persistent Dish')
        self.assertEqual(dish.average_rating(), 4.0)