from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm, ProfileForm
from accounts.models import Profile
from nutrition.models import MealPlan
from nutrition.meal_generator import generate_meal_plan
from nutrition.expert_system import run_expert_system
from nutrition.shopping_list import generate_shopping_list
from django.http import JsonResponse


def register_view(request):
    if request.method == 'POST':
        human_check = request.POST.get('human_check')

        if human_check != 'verified':
            form = RegisterForm(request.POST)
            form.add_error(None, "Please complete the human verification check.")
            return render(request, 'accounts/register.html', {'form': form})

        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('profile_setup')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


@login_required
def profile_setup_view(request):
    profile = Profile.objects.filter(user=request.user).first()

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            new_profile = form.save(commit=False)
            new_profile.user = request.user
            new_profile.save()
            return redirect('dashboard')
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'accounts/profile_setup.html', {'form': form})


@login_required
def dashboard_view(request):
    profile = Profile.objects.filter(user=request.user).first()
    if profile is None:
        return redirect('profile_setup')

    latest_plan = MealPlan.objects.filter(profile=profile).order_by('-created_at').first()
    analysis = run_expert_system(profile)

    return render(request, 'accounts/dashboard.html', {
        'profile': profile,
        'plan': latest_plan,
        'analysis': analysis,
    })


@login_required
def generate_plan_view(request):
    profile = Profile.objects.filter(user=request.user).first()
    if profile is None:
        return redirect('profile_setup')

    generate_meal_plan(profile)
    return redirect('dashboard')


@login_required
def shopping_list_view(request):
    profile = Profile.objects.filter(user=request.user).first()
    if profile is None:
        return redirect('profile_setup')

    latest_plan = MealPlan.objects.filter(profile=profile).order_by('-created_at').first()

    if not latest_plan:
        return redirect('dashboard')

    shopping_data = generate_shopping_list(latest_plan)

    return render(request, 'accounts/shopping_list.html', {
        'shopping_data': shopping_data,
        'plan': latest_plan,
    })
    from django.http import JsonResponse
from nutrition.models import Rating


@login_required
def rate_dish_view(request):
    if request.method == 'POST':
        dish_id = request.POST.get('dish_id')
        stars = request.POST.get('stars')

        if not dish_id or not stars:
            return JsonResponse({'success': False, 'error': 'Missing data'}, status=400)

        try:
            stars = int(stars)
            if stars < 1 or stars > 5:
                raise ValueError
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Invalid rating'}, status=400)

        rating, created = Rating.objects.update_or_create(
            user=request.user,
            dish_id=dish_id,
            defaults={'stars': stars}
        )

        return JsonResponse({'success': True, 'stars': rating.stars})

    return JsonResponse({'success': False, 'error': 'POST required'}, status=405)