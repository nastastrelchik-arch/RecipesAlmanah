from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from recipes.models import Recipe, Favorite
from comments.models import Comment
from django.views.decorators.http import require_http_methods
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm


# Обработка регистрации новых пользователей на сайте
def register(request):
    if request.method == 'POST':
        # Обработка данных формы
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            # Сохранение пользователя
            user = form.save()
            username = form.cleaned_data.get('username')
            # Автоматический вход после регистрации
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            if user is not None:
                login(request, user)

            messages.success(request, f'Аккаунт {username} был успешно создан!')
            # Перенаправка на главную страницу
            return redirect('recipes:home')
    else:
        # Показ пустой формы
        form = UserRegisterForm()
    # Рендеринг формы
    return render(request, 'users/register.html', {'form': form})


# Отображает профиль пользователя
@login_required
def profile(request):
    try:
        # Получаем рецепты пользователя
        user_recipes = Recipe.objects.filter(author=request.user).order_by('-created_at')

        # Получаем комментарии пользователя
        user_comments = Comment.objects.filter(author=request.user)

        # Получаем избранные рецепты пользователя
        user_favorites = Favorite.objects.filter(user=request.user)

        # Получаем список рецептов из избранного для отображения
        favorite_recipes = Recipe.objects.filter(favorite__user=request.user)

        # Отладочная информация
        print(f"User: {request.user}")
        print(f"User recipes count: {user_recipes.count()}")
        print(f"User favorites count: {user_favorites.count()}")

        context = {
            'title': 'Профиль пользователя',
            'user_recipes': user_recipes,
            'user_comments': user_comments,
            'user_favorites': user_favorites,
            'favorite_recipes': favorite_recipes,
        }

        return render(request, 'users/profile.html', context)
    except Exception as e:
        messages.error(request, f'Произошла ошибка при загрузке профиля: {str(e)}')
        return render(request, 'users/profile.html', {
            'user_recipes': [],
            'user_comments': [],
            'user_favorites': [],
            'favorite_recipes': [],
        })

# Отдельная функция для редактирования профиля
@login_required
def edit_profile(request):
    try:
        if request.method == 'POST':
            # Форма для обновления основных данных пользователя
            u_form = UserUpdateForm(request.POST, instance=request.user)
            # Форма для обновления профиля
            p_form = ProfileUpdateForm(request.POST,
                                       request.FILES,
                                       instance=request.user.profile
                                       )

            # Валидация и сохранение в БД
            if u_form.is_valid() and p_form.is_valid():
                u_form.save()
                p_form.save()
                messages.success(request, 'Ваш профиль был успешно изменён')
                return redirect('users:profile')
            else:
                messages.error(request, 'Пожалуйста, исправьте ошибки в форме')
        # Обработка невалидных данных
        else:
            u_form = UserUpdateForm(instance=request.user)
            p_form = ProfileUpdateForm(instance=request.user.profile)

        context = {
            'u_form': u_form,
            'p_form': p_form,
            'title': 'Редактирование профиля',
        }

        return render(request, 'users/edit_profile.html', context)
    except Exception as e:
        messages.error(request, f'Произошла ошибка при загрузке формы редактирования: {str(e)}')
        return redirect('users:profile')


@login_required
def remove_favorite(request, pk):
    try:
        recipe = get_object_or_404(Recipe, pk=pk)
        favorite = Favorite.objects.filter(user=request.user, recipe=recipe)

        if favorite.exists():
            favorite.delete()
            messages.success(request, 'Рецепт удален из избранного.')
        else:
            messages.error(request, 'Этот рецепт не был в избранном.')
    except Exception as e:
        messages.error(request, f'Ошибка при удалении из избранного: {str(e)}')

    return redirect('users:profile')

@require_http_methods(['GET', 'POST'])
def custom_logout(request):
    logout(request)
    return redirect('recipes:home')