from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from recipes.models import Recipe, Favorite
from comments.models import Comment
from django.views.decorators.http import require_http_methods
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm

#Обработка регистрации новых пользователей на сайте
def register(request):
    if request.method == 'POST':
        #Обработка данных формы
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            #Сохранение пользователя
            user = form.save()
            username = form.cleaned_data.get('username')
            #Автоматический вход после регистрации
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            if user is not None:
                login(request, user)

            messages.success(request, f'Аккаунт {username} был успешно создан!')
            #Перенаправка на главную страницу
            return redirect('recipes:home')
    else:
        #Показ пустой формы
        form = UserRegisterForm()
    #Рендеринг формы
    return render(request, 'users/register.html', {'form': form})


#Отображает профиль пользователя с обновлением данных
#Защита доступа(требует аутентификации)
@login_required
def profile(request):
    try:
    #Получаем рецепты пользователя
        user_recipes = Recipe.objects.filter(author=request.user).order_by('-created_at')

    #Полусаем комментарии пользователя
        user_comments = Comment.objects.filter(author=request.user)

    #Получаем избранные рецепты пользователя
        user_favorites = Favorite.objects.filter(user=request.user)

        if request.method == 'POST':
        #Форма для обновления основных данных пользователя
            u_form = UserUpdateForm(request.POST, instance=request.user)
        #Форма для обновления профиля
            p_form = ProfileUpdateForm(request.POST,
                                   request.FILES,
                                   instance=request.user.profile
            )

        #Валидация и сохранение в БД
            if u_form.is_valid() and p_form.is_valid():
                u_form.save()
                p_form.save()
                messages.success(request, 'Ваш профиль был успешно изменён')
                return redirect('users:profile')
            else: messages.error(request, 'Пожалуйста, исправьте ошибки в форме')
        #Обработка невалидных данных
        else:
            u_form = UserUpdateForm(instance=request.user)
            p_form = ProfileUpdateForm(instance=request.user.profile)

#Получаем данные пользователя для статистики
        context = {
        'u_form': u_form,
        'p_form': p_form,
        'title': 'Профиль пользователя',
        'user_recipes': user_recipes,
        'user_comments': user_comments,
        'user_favorites': user_favorites,
        }

        return render(request, 'users/profile.html', context)
    except Exception as e:
        messages.error(request, f'Произошла ошибка при загрузке профиля: {str(e)}')
        return render(request, 'users/profile.html', {
            'user_recipes': [],
            'user_comments': [],
            'user_favorites': [],
        })

@require_http_methods(['GET', 'POST'])
def custom_logout(request):
    logout(request)
    return redirect('recipes:home')
