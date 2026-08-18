from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):

    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]

    GOAL_CHOICES = [
        ('lose', 'Lose Weight'),
        ('maintain', 'Maintain Weight'),
        ('gain', 'Gain Weight'),
    ]

    REGION_CHOICES = [
        ('yoruba', 'Yoruba'),
        ('igbo', 'Igbo'),
        ('hausa', 'Hausa'),
        ('general', 'General / No Preference'),
    ]

    SWALLOW_CHOICES = [
        ('swallow', 'Swallow'),
        ('rice', 'Rice based'),
        ('yam', 'Yam based'),
        ('both', 'Both'),
    ]

    SPICE_CHOICES = [
        ('mild', 'Mild'),
        ('medium', 'Medium'),
        ('very_spicy', 'Very Spicy'),
    ]

    PROTEIN_CHOICES = [
        ('chicken', 'Chicken'),
        ('fish', 'Fish'),
        ('beef', 'Beef'),
        ('turkey', 'Turkey'),
        ('none', 'No meat (vegetarian)'),
    ]

    BUDGET_CHOICES = [
        ('budget', 'Budget friendly (under N5000)'),
        ('moderate', 'Moderate (N5000 - N15000)'),
        ('flexible', 'Flexible (above N15000)'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Physiological needs
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    weight_kg = models.FloatField(help_text="Weight in kilograms")
    height_cm = models.FloatField(help_text="Height in centimeters")

    # Goal
    goal = models.CharField(max_length=10, choices=GOAL_CHOICES, default='maintain')

    # Taste preferences
    swallow_preference = models.CharField(max_length=10, choices=SWALLOW_CHOICES, default='both')
    spice_level = models.CharField(max_length=15, choices=SPICE_CHOICES, default='medium')
    protein_preference = models.CharField(max_length=10, choices=PROTEIN_CHOICES, default='chicken')

    # Cultural characteristics
    cultural_region = models.CharField(max_length=10, choices=REGION_CHOICES, default='general')

    # Economic constraints
    budget_level = models.CharField(max_length=10, choices=BUDGET_CHOICES, default='moderate')

    # Allergies (simple boolean flags — good enough for now, can normalize later)
    allergy_gluten = models.BooleanField(default=False)
    allergy_nuts = models.BooleanField(default=False)
    allergy_fish = models.BooleanField(default=False)
    allergy_eggs = models.BooleanField(default=False)
    allergy_dairy = models.BooleanField(default=False)
    allergy_soy = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def bmi(self):
        height_m = self.height_cm / 100
        return round(self.weight_kg / (height_m ** 2), 1)

    def bmr(self):
        if self.gender == 'male':
            return 88.36 + (13.4 * self.weight_kg) + (4.8 * self.height_cm) - (5.7 * self.age)
        else:
            return 447.6 + (9.2 * self.weight_kg) + (3.1 * self.height_cm) - (4.3 * self.age)