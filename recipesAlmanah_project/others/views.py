from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Article, Recommendation, Statistic
from .forms import ArticleForm
from recipes.models import Hashtag, Recipe
from users.models import User
from django.db.models import Count, Q
import json
from datetime import datetime, timedelta


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
    # ... существующий код рекомендаций ...
    recommendations = Recommendation.objects.get_recommendations_for_user(request.user)

    if not recommendations:
        context = {
            'recommendations': [],
            'message': 'Пока недостаточно данных для формирования рекомендаций. Добавьте рецепты в избранное!',
            'debug_info': {
                'favorite_count': request.user.favorite_set.count(),
                'hashtag_count': Hashtag.objects.filter(
                    recipe__in=[fav.recipe for fav in request.user.favorite_set.all()]).distinct().count(),
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


def _generate_site_statistics(self):
    """Сгенерировать статистику сайта"""
    from recipes.models import Favorite

    # Топ-10 популярных рецептов (по количеству в избранном)
    popular_recipes = Recipe.objects.annotate(
        fav_count_annotated=Count('favorite', distinct=True)
    ).filter(
        fav_count_annotated__gt=0
    ).order_by('-fav_count_annotated')[:10]

    # Новинки (последние 10 рецептов)
    new_recipes = Recipe.objects.all().order_by('-created_at')[:10]

    # Топ-10 популярных хештегов (по количеству использований в рецептах)
    popular_hashtags = Hashtag.objects.annotate(
        usage_count=Count('recipe', distinct=True)
    ).filter(
        usage_count__gt=0
    ).order_by('-usage_count')[:10]

    # Топ-3 популярных автора - ИСПРАВЛЕННЫЙ ЗАПРОС
    from django.db.models import Subquery, OuterRef

    # Подзапрос для количества рецептов
    recipe_count_subquery = Recipe.objects.filter(
        author_id=OuterRef('id')
    ).values('author_id').annotate(
        count=Count('id', distinct=True)
    ).values('count')[:1]

    # Подзапрос для количества избранного - ИСПРАВЛЕННЫЙ
    # Считаем только уникальные связи автор-избранное
    favorite_count_subquery = Favorite.objects.filter(
        recipe__author_id=OuterRef('id')
    ).values('recipe__author_id').annotate(
        count=Count('id', distinct=True)
    ).values('count')[:1]

    popular_authors = User.objects.annotate(
        recipe_count=Subquery(recipe_count_subquery),
        total_favorites=Subquery(favorite_count_subquery)
    ).filter(
        recipe_count__isnull=False
    ).order_by('-total_favorites', '-recipe_count')[:3]

    # Дополнительная статистика
    total_recipes = Recipe.objects.count()
    total_users = User.objects.count()
    total_favorites = Favorite.objects.count()

    # Статистика за последнюю неделю
    week_ago = datetime.now() - timedelta(days=7)
    new_recipes_week = Recipe.objects.filter(created_at__gte=week_ago).count()
    new_users_week = User.objects.filter(date_joined__gte=week_ago).count()

    # ОТЛАДКА: выведем реальные значения для проверки
    print("=== DEBUG: REAL FAVORITE COUNTS ===")
    for author in popular_authors:
        real_favorite_count = Favorite.objects.filter(
            recipe__author=author
        ).count()
        print(f"Author: {author.username}, Subquery count: {author.total_favorites}, Real count: {real_favorite_count}")

    return {
        'popular_recipes': list(popular_recipes),
        'new_recipes': list(new_recipes),
        'popular_hashtags': list(popular_hashtags),
        'popular_authors': list(popular_authors),
        'total_recipes': total_recipes,
        'total_users': total_users,
        'total_favorites': total_favorites,
        'new_recipes_week': new_recipes_week,
        'new_users_week': new_users_week,
    }

@user_passes_test(is_staff_user)
def statistics_view(request):
    """Страница статистики для администраторов"""
    try:
        # Используем менеджер модели Statistic для получения статистики
        statistics = Statistic.objects.get_site_statistics()
        detailed_stats = Statistic.objects.get_detailed_statistics()

        context = {
            'statistics': statistics,
            'detailed_stats': detailed_stats,
        }
        return render(request, 'others/statistics.html', context)
    except Exception as e:
        # Если есть ошибка, показываем сообщение
        messages.error(request, f'Ошибка при загрузке статистики: {str(e)}')
        # Возвращаем пустую статистику
        context = {
            'statistics': {
                'popular_recipes': [],
                'new_recipes': [],
                'popular_hashtags': [],
                'popular_authors': [],
                'total_recipes': 0,
                'total_users': 0,
                'total_favorites': 0,
                'new_recipes_week': 0,
                'new_users_week': 0,
            },
            'detailed_stats': {
                'monthly_stats': [],
                'active_users': [],
                'most_commented': [],
            }
        }
        return render(request, 'others/statistics.html', context)


def public_statistics_view(request):
    """Публичная страница статистики для всех пользователей"""
    try:
        statistics = Statistic.objects.get_site_statistics()

        context = {
            'statistics': statistics,
        }
        return render(request, 'others/public_statistics.html', context)
    except Exception as e:
        messages.error(request, f'Ошибка при загрузке статистики: {str(e)}')
        context = {
            'statistics': {
                'popular_recipes': [],
                'new_recipes': [],
                'popular_hashtags': [],
                'popular_authors': [],
                'total_recipes': 0,
                'total_users': 0,
                'total_favorites': 0,
                'new_recipes_week': 0,
                'new_users_week': 0,
            }
        }
        return render(request, 'others/public_statistics.html', context)


def update_statistics(request):
    """Принудительное обновление статистики (для админов)"""
    if not request.user.is_staff:
        messages.error(request, 'У вас нет прав для выполнения этого действия.')
        return redirect('others:statistics')

    try:
        Statistic.update_site_statistics()
        messages.success(request, 'Статистика успешно обновлена!')
    except Exception as e:
        messages.error(request, f'Ошибка при обновлении статистики: {str(e)}')

    return redirect('others:statistics')


@login_required
def search_recipes(request):
    """Обработка поиска рецептов с сохранением статистики"""
    from .models import SearchQuery, HashtagSearch

    query = request.GET.get('q', '').strip()
    hashtag_query = request.GET.get('hashtag', '').strip()

    search_results = []

    if query:
        # Сохраняем поисковый запрос
        SearchQuery.objects.create(
            query=query,
            user=request.user if request.user.is_authenticated else None
        )

        # Логика поиска по рецептам
        search_results = Recipe.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(ingredients__name__icontains=query)
        ).filter(is_published=True)

    elif hashtag_query:
        # Обработка поиска по хештегам
        hashtag_name = hashtag_query.lower().replace('#', '')

        try:
            hashtag = Hashtag.objects.get(name=hashtag_name)
            # Обновляем статистику поиска по хештегу
            hashtag_search, created = HashtagSearch.objects.get_or_create(
                hashtag=hashtag
            )
            hashtag_search.search_count += 1
            hashtag_search.save()

            search_results = Recipe.objects.filter(
                hashtags=hashtag,
                is_published=True
            )

        except Hashtag.DoesNotExist:
            search_results = Recipe.objects.none()

    context = {
        'search_results': search_results,
        'query': query,
        'hashtag_query': hashtag_query,
    }

    return render(request, 'others/search_results.html', context)