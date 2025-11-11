
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Article, Recommendation
from .forms import ArticleForm
from recipes.models import Hashtag


def articles_list(request):
    articles = Article.objects.filter(is_published=True).order_by('-published_at')
    return render(request, 'others/articles_list.html', {'articles': articles})


def article_detail(request, pk):
    article = get_object_or_404(Article, pk=pk, is_published=True)
    # Увеличиваем счетчик просмотров
    article.views_count += 1
    article.save()
    return render(request, 'others/article_detail.html', {'article': article})


@login_required
def create_article(request):
    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            article.save()
            form.save_m2m()  # для ManyToMany поля hashtags
            messages.success(request, 'Статья успешно создана!')
            return redirect('others:article-detail', pk=article.pk)
    else:
        form = ArticleForm()
    return render(request, 'others/article_form.html', {'form': form})


@login_required
def edit_article(request, pk):
    article = get_object_or_404(Article, pk=pk, author=request.user)
    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES, instance=article)
        if form.is_valid():
            form.save()
            messages.success(request, 'Статья успешно обновлена!')
            return redirect('others:article-detail', pk=article.pk)
    else:
        form = ArticleForm(instance=article)
    return render(request, 'others/article_form.html', {'form': form})


@login_required
def recommendations_list(request):
    """Страница с рекомендациями для пользователя"""

    # Отладочная информация
    print(f"=== ДЕБАГ РЕКОМЕНДАЦИЙ ДЛЯ {request.user.username} ===")

    # Проверяем избранные рецепты
    favorite_recipes = request.user.favorite_set.all()
    print(f"Избранных рецептов: {favorite_recipes.count()}")
    for fav in favorite_recipes:
        print(f" - {fav.recipe.title}: {[tag.name for tag in fav.recipe.hashtags.all()]}")

    # Проверяем хештеги из избранного
    favorite_hashtags = Hashtag.objects.filter(recipe__in=[fav.recipe for fav in favorite_recipes]).distinct()
    print(f"Хештеги в избранном: {[tag.name for tag in favorite_hashtags]}")

    recommendations = Recommendation.objects.get_recommendations_for_user(request.user)
    print(f"Рекомендаций из кэша: {len(recommendations)}")

    # Если нет рекомендаций, показываем сообщение
    if not recommendations:
        context = {
            'recommendations': [],
            'message': 'Пока недостаточно данных для формирования рекомендаций. Добавьте рецепты в избранное!',
            'debug_info': {
                'favorite_count': favorite_recipes.count(),
                'hashtag_count': favorite_hashtags.count(),
            }
        }
    else:
        context = {
            'recommendations': recommendations,
            'message': None,
            'debug_info': None
        }

    return render(request, 'others/recommendations_list.html', context)


def get_quick_recommendations(user, limit=3):
    """Быстрые рекомендации для главной страницы"""
    if not user.is_authenticated:
        return None

    recommendations = Recommendation.objects.get_recommendations_for_user(user)
    return recommendations[:limit] if recommendations else None


# Проверка для админских функций
def is_staff_user(user):
    return user.is_staff


@user_passes_test(is_staff_user)
def statistics_view(request):
    # Здесь будет логика для отображения статистики
    return render(request, 'others/statistics.html')