from django.db import models
from django.contrib.auth.models import User
from accounts.models import Profile


class Ingredient(models.Model):

    COST_CHOICES = [
        ('budget', 'Budget'),
        ('moderate', 'Moderate'),
        ('premium', 'Premium'),
    ]

    name = models.CharField(max_length=100, unique=True)
    cost_level = models.CharField(max_length=10, choices=COST_CHOICES, default='moderate')
    approximate_cost_naira = models.PositiveIntegerField(help_text="Estimated cost per typical unit")
    is_available_nationwide = models.BooleanField(default=True)
    is_seasonal = models.BooleanField(default=False)
    season = models.CharField(max_length=20, blank=True, help_text="e.g. harmattan, rainy, all year")

    def __str__(self):
        return self.name


class Dish(models.Model):

    MEAL_TYPE_CHOICES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('snack', 'Snack'),
    ]

    REGION_CHOICES = [
        ('yoruba', 'Yoruba'),
        ('igbo', 'Igbo'),
        ('hausa', 'Hausa'),
        ('general', 'General'),
    ]

    COST_CHOICES = [
        ('budget', 'Budget'),
        ('moderate', 'Moderate'),
        ('premium', 'Premium'),
    ]

    SPICE_CHOICES = [
        ('mild', 'Mild'),
        ('medium', 'Medium'),
        ('very_spicy', 'Very Spicy'),
    ]

    name = models.CharField(max_length=150)
    meal_type = models.CharField(max_length=10, choices=MEAL_TYPE_CHOICES)
    region = models.CharField(max_length=10, choices=REGION_CHOICES, default='general')
    cost_level = models.CharField(max_length=10, choices=COST_CHOICES, default='moderate')
    spice_level = models.CharField(max_length=15, choices=SPICE_CHOICES, default='medium')

    # Nutrition per serving
    calories = models.PositiveIntegerField()
    protein_grams = models.FloatField()
    carb_grams = models.FloatField()
    fat_grams = models.FloatField()

    # Classification for filtering
    is_vegetarian = models.BooleanField(default=False)
    contains_gluten = models.BooleanField(default=False)
    contains_nuts = models.BooleanField(default=False)
    contains_fish = models.BooleanField(default=False)
    contains_eggs = models.BooleanField(default=False)
    contains_dairy = models.BooleanField(default=False)
    contains_soy = models.BooleanField(default=False)

    is_seasonal = models.BooleanField(default=False)
    season = models.CharField(max_length=20, blank=True)

    ingredients = models.ManyToManyField(Ingredient, through='DishIngredient')

    def __str__(self):
        return self.name

    def average_rating(self):
        ratings = self.rating_set.all()
        if not ratings:
            return None
        return round(sum(r.stars for r in ratings) / len(ratings), 1)


class DishIngredient(models.Model):
    """Links a Dish to its Ingredients with a quantity — the recipe itself."""

    dish = models.ForeignKey(Dish, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity = models.CharField(max_length=50, help_text="e.g. '2 cups', '100g', '1 medium'")

    def __str__(self):
        return f"{self.quantity} {self.ingredient.name} for {self.dish.name}"


class MealPlan(models.Model):
    """A single generated 7-day plan for a user."""

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    daily_calorie_target = models.PositiveIntegerField()
    daily_protein_target = models.PositiveIntegerField()
    daily_carb_target = models.PositiveIntegerField()
    daily_fat_target = models.PositiveIntegerField()

    def __str__(self):
        return f"MealPlan for {self.profile.user.username} ({self.created_at.date()})"


class MealPlanEntry(models.Model):
    """One dish, on one day, for one meal slot, within a MealPlan."""

    DAY_CHOICES = [(i, f"Day {i}") for i in range(1, 8)]
    meal_plan = models.ForeignKey(MealPlan, on_delete=models.CASCADE, related_name='entries')
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE)
    day_number = models.PositiveSmallIntegerField(choices=DAY_CHOICES)
    meal_type = models.CharField(max_length=10, choices=Dish.MEAL_TYPE_CHOICES)

    def __str__(self):
        return f"Day {self.day_number} {self.meal_type}: {self.dish.name}"


class Rating(models.Model):
    """User's star rating of a dish — feeds the data-driven learning layer."""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE)
    stars = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'dish')  # one rating per user per dish, re-rating updates it

    def __str__(self):
        return f"{self.user.username} rated {self.dish.name}: {self.stars} stars"
# Create your models here.
