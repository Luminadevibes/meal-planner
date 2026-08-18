from django.test import TestCase
from django.contrib.auth.models import User
from accounts.models import Profile
from accounts.forms import RegisterForm, ProfileForm


class ProfileModelUnitTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pw12345!')

    def create_profile(self, gender='male', age=30, weight=80.0, height=180.0):
        return Profile.objects.create(
            user=self.user,
            age=age,
            gender=gender,
            weight_kg=weight,
            height_cm=height,
            goal='maintain',
        )

    def test_bmi_calculation(self):
        profile = self.create_profile()
        self.assertAlmostEqual(profile.bmi(), 24.7, places=1)

    def test_bmr_male(self):
        profile = self.create_profile(gender='male', age=30, weight=80, height=180)
        expected = 88.36 + (13.4 * 80) + (4.8 * 180) - (5.7 * 30)
        self.assertAlmostEqual(profile.bmr(), expected, places=2)

    def test_bmr_female(self):
        profile = self.create_profile(gender='female', age=28, weight=65, height=165)
        expected = 447.6 + (9.2 * 65) + (3.1 * 165) - (4.3 * 28)
        self.assertAlmostEqual(profile.bmr(), expected, places=2)

    def test_profile_str(self):
        profile = self.create_profile()
        self.assertEqual(str(profile), "alice's Profile")


class RegisterFormUnitTests(TestCase):
    def test_valid_registration_data(self):
        form = RegisterForm(data={
            'username': 'bob',
            'email': 'bob@example.com',
            'password1': 'strongpass123!',
            'password2': 'strongpass123!',
        })
        self.assertTrue(form.is_valid())

    def test_missing_email_is_invalid(self):
        form = RegisterForm(data={
            'username': 'bob',
            'email': '',
            'password1': 'strongpass123!',
            'password2': 'strongpass123!',
        })
        self.assertFalse(form.is_valid())


class ProfileFormUnitTests(TestCase):
    def test_valid_profile_data(self):
        form = ProfileForm(data={
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
        self.assertTrue(form.is_valid())

    def test_missing_required_fields_is_invalid(self):
        form = ProfileForm(data={})
        self.assertFalse(form.is_valid())