from django.test import TestCase
from django.contrib.auth.models import User
from accounts.models import Profile
from nutrition.models import Dish, Ingredient, DishIngredient, MealPlan, MealPlanEntry, Rating
from nutrition.expert_system import get_bmi_category, get_age_group, run_expert_system
from nutrition.meal_generator import filter_dishes_for_profile, pick_dish, generate_meal_plan
from nutrition.shopping_list import generate_shopping_list


def make_dish(name, meal_type='lunch', region='general', cost_level='moderate',
              contains_gluten=False, contains_nuts=False, is_vegetarian=False,
              calories=400, protein=25.0, carb=40.0, fat=15.0):
    return Dish.objects.create(
        name=name,
        meal_type=meal_type,
        region=region,
        cost_level=cost_level,
        calories=calories,
        protein_grams=protein,
        carb_grams=carb,
        fat_grams=fat,
        contains_gluten=contains_gluten,
        contains_nuts=contains_nuts,
        is_vegetarian=is_vegetarian,
    )


class ExpertSystemUnitTests(TestCase):
    def test_bmi_category_boundaries(self):
        self.assertEqual(get_bmi_category(17), 'underweight')
        self.assertEqual(get_bmi_category(22), 'normal')
        self.assertEqual(get_bmi_category(27), 'overweight')
        self.assertEqual(get_bmi_category(35), 'obese')

    def test_age_group_boundaries(self):
        self.assertEqual(get_age_group(15), 'teen')
        self.assertEqual(get_age_group(25), 'young_adult')
        self.assertEqual(get_age_group(45), 'middle_aged')
        self.assertEqual(get_age_group(60), 'senior')

    def test_run_expert_system_returns_expected_keys(self):
        user = User.objects.create_user(username='expert', password='pw12345!')
        profile = Profile.objects.create(
            user=user, age=30, gender='male', weight_kg=80, height_cm=180, goal='maintain'
        )
        result = run_expert_system(profile)

        self.assertAlmostEqual(result['bmi'], profile.bmi(), places=1)
        self.assertEqual(result['bmi_category'], 'normal')
        self.assertEqual(result['age_group'], 'young_adult')
        self.assertIn('advice', result)
        self.assertGreaterEqual(result['daily_calories'], 1200)

    def test_daily_calories_floor_at_1200(self):
        user = User.objects.create_user(username='floor', password='pw12345!')
        profile = Profile.objects.create(
            user=user, age=60, gender='female', weight_kg=100, height_cm=165, goal='maintain'
        )
        result = run_expert_system(profile)
        self.assertEqual(result['bmi_category'], 'obese')
        self.assertEqual(result['daily_calories'], 1200)


class DishModelUnitTests(TestCase):
    def test_average_rating_none_when_no_ratings(self):
        dish = make_dish('Jollof Rice')
        self.assertIsNone(dish.average_rating())

    def test_average_rating(self):
        dish = make_dish('Jollof Rice')
        user = User.objects.create_user(username='rater', password='pw12345!')
        Rating.objects.create(user=user, dish=dish, stars=4)
        other = User.objects.create_user(username='rater2', password='pw12345!')
        Rating.objects.create(user=other, dish=dish, stars=5)
        self.assertEqual(dish.average_rating(), 4.5)


class MealGeneratorUnitTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='gen', password='pw12345!')

    def make_profile(self, **kwargs):
        defaults = dict(age=30, gender='male', weight_kg=80, height_cm=180, goal='maintain')
        defaults.update(kwargs)
        return Profile.objects.create(user=self.user, **defaults)

    def test_allergy_hard_exclusion(self):
        make_dish('Gluten Dish', contains_gluten=True)
        make_dish('Safe Dish', contains_gluten=False)
        profile = self.make_profile(allergy_gluten=True)
        dishes = filter_dishes_for_profile(profile)
        names = list(dishes.values_list('name', flat=True))
        self.assertNotIn('Gluten Dish', names)
        self.assertIn('Safe Dish', names)

    def test_budget_filter(self):
        make_dish('Cheap Dish', cost_level='budget')
        make_dish('Pricey Dish', cost_level='premium')
        profile = self.make_profile(budget_level='budget')
        names = list(filter_dishes_for_profile(profile).values_list('name', flat=True))
        self.assertIn('Cheap Dish', names)
        self.assertNotIn('Pricey Dish', names)

    def test_vegetarian_soft_filter(self):
        make_dish('Veg Dish', is_vegetarian=True)
        make_dish('Meat Dish', is_vegetarian=False)
        profile = self.make_profile(protein_preference='none')
        names = list(filter_dishes_for_profile(profile).values_list('name', flat=True))
        self.assertIn('Veg Dish', names)
        self.assertNotIn('Meat Dish', names)

    def test_region_filter(self):
        make_dish('Yoruba Dish', region='yoruba')
        make_dish('Igbo Dish', region='igbo')
        profile = self.make_profile(cultural_region='igbo')
        names = list(filter_dishes_for_profile(profile).values_list('name', flat=True))
        self.assertIn('Igbo Dish', names)
        self.assertNotIn('Yoruba Dish', names)

    def test_pick_dish_prefers_fresh(self):
        dish_a = make_dish('Dish A')
        dish_b = make_dish('Dish B')
        chosen = pick_dish([dish_a, dish_b], [dish_a.id])
        self.assertEqual(chosen.id, dish_b.id)

    def test_pick_dish_empty_returns_none(self):
        self.assertIsNone(pick_dish([], []))

    def test_generate_meal_plan_creates_full_week(self):
        for slot in ['breakfast', 'lunch', 'dinner', 'snack']:
            make_dish(f'{slot.title()} 1', meal_type=slot)
            make_dish(f'{slot.title()} 2', meal_type=slot)

        profile = self.make_profile()
        plan = generate_meal_plan(profile)

        self.assertEqual(plan.daily_calorie_target, run_expert_system(profile)['daily_calories'])
        self.assertEqual(plan.entries.count(), 28)
        self.assertEqual(plan.entries.filter(day_number=1).count(), 4)

        for slot in ['breakfast', 'lunch', 'dinner', 'snack']:
            slot_dishes = set(
                plan.entries.filter(meal_type=slot).values_list('dish_id', flat=True)
            )
            self.assertEqual(len(slot_dishes), 2, f'{slot} should use both dishes for variety')

    def test_generate_meal_plan_skips_empty_slots(self):
        make_dish('Only Lunch', meal_type='lunch')
        profile = self.make_profile()
        plan = generate_meal_plan(profile)
        self.assertEqual(plan.entries.count(), 7)


class ShoppingListUnitTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='shop', password='pw12345!')

    def test_shopping_list_groups_and_totals(self):
        rice = Ingredient.objects.create(name='Rice', cost_level='budget', approximate_cost_naira=800)
        chicken = Ingredient.objects.create(name='Chicken', cost_level='moderate', approximate_cost_naira=2000)
        dish = make_dish('Jollof Rice')
        DishIngredient.objects.create(dish=dish, ingredient=rice, quantity='2 cups')
        DishIngredient.objects.create(dish=dish, ingredient=chicken, quantity='500g')

        profile = Profile.objects.create(
            user=self.user, age=30, gender='male', weight_kg=80, height_cm=180, goal='maintain'
        )
        plan = MealPlan.objects.create(
            profile=profile,
            daily_calorie_target=2000,
            daily_protein_target=100,
            daily_carb_target=200,
            daily_fat_target=60,
        )
        MealPlanEntry.objects.create(meal_plan=plan, dish=dish, day_number=1, meal_type='lunch')

        result = generate_shopping_list(plan)
        self.assertEqual(set(result['grouped'].keys()), {'budget', 'moderate'})
        self.assertEqual(result['total_estimated_cost'], 2800)

    def test_shopping_list_empty_plan(self):
        profile = Profile.objects.create(
            user=self.user, age=30, gender='male', weight_kg=80, height_cm=180, goal='maintain'
        )
        plan = MealPlan.objects.create(
            profile=profile,
            daily_calorie_target=2000,
            daily_protein_target=100,
            daily_carb_target=200,
            daily_fat_target=60,
        )
        result = generate_shopping_list(plan)
        self.assertEqual(result['grouped'], {})
        self.assertEqual(result['total_estimated_cost'], 0)