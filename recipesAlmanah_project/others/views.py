from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Article, Recommendation, Statistic, ArticleProposal, ArticleImage
from .forms import ArticleForm, ArticleProposalForm, ArticleProposalReviewForm
from recipes.models import Hashtag, Recipe
from users.models import User
from django.db.models import Count, Q
import json
from datetime import datetime, timedelta
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone


def articles_list(request):
    """Список опубликованных статей"""
    articles = Article.objects.filter(status='published').order_by('-published_at')
    return render(request, 'others/articles_list.html', {'articles': articles})


def article_detail(request, pk):
    """Детальная страница статьи"""
    article = get_object_or_404(Article, pk=pk)

    # Проверяем доступ к статье
    if article.status != 'published' and not (request.user.is_staff or request.user == article.author):
        messages.error(request, 'Эта статья недоступна для просмотра.')
        return redirect('others:articles-list')

    # Увеличиваем счетчик просмотров
    article.views_count += 1
    article.save()

    return render(request, 'others/article_detail.html', {'article': article})


@user_passes_test(lambda u: u.is_staff)
def create_article(request):
    """Создание статьи (только для админов)"""
    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            article.save()
            form.save_m2m()  # для ManyToMany поля hashtags

            # Обрабатываем дополнительные изображения
            additional_images = request.FILES.getlist('additional_images')
            for image_file in additional_images:
                ArticleImage.objects.create(
                    article=article,
                    image=image_file
                )

            messages.success(request, 'Статья успешно создана!')
            return redirect('others:article-detail', pk=article.pk)
    else:
        form = ArticleForm()
    return render(request, 'others/article_form.html', {'form': form})


@user_passes_test(lambda u: u.is_staff)
def edit_article(request, pk):
    """Редактирование статьи (только для админов)"""
    article = get_object_or_404(Article, pk=pk)
    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES, instance=article)
        if form.is_valid():
            form.save()

            # Обрабатываем дополнительные изображения
            additional_images = request.FILES.getlist('additional_images')
            for image_file in additional_images:
                ArticleImage.objects.create(
                    article=article,
                    image=image_file
                )

            messages.success(request, 'Статья успешно обновлена!')
            return redirect('others:article-detail', pk=article.pk)
    else:
        form = ArticleForm(instance=article)
    return render(request, 'others/article_form.html', {'form': form})


@user_passes_test(lambda u: u.is_staff)
def delete_article_image(request, pk):
    """Удаление дополнительного изображения статьи"""
    article_image = get_object_or_404(ArticleImage, pk=pk)
    article_pk = article_image.article.pk

    if request.method == 'POST':
        article_image.delete()
        messages.success(request, 'Изображение успешно удалено.')
        return redirect('others:edit-article', pk=article_pk)

    # Если GET запрос, показываем страницу подтверждения
    return render(request, 'others/confirm_delete_image.html', {
        'article_image': article_image
    })


@user_passes_test(lambda u: u.is_staff)
def article_management(request):
    """Управление статьями для админов"""
    articles = Article.objects.all().order_by('-published_at')
    pending_articles = Article.objects.filter(status='pending_review')
    draft_articles = Article.objects.filter(status='draft')

    context = {
        'articles': articles,
        'pending_articles': pending_articles,
        'draft_articles': draft_articles,
    }
    return render(request, 'others/article_management.html', context)


def propose_article(request):
    """Форма предложения статьи от пользователей"""
    if request.method == 'POST':
        form = ArticleProposalForm(request.POST)
        if form.is_valid():
            proposal = form.save()
            messages.success(request, 'Ваше предложение успешно отправлено! Мы свяжемся с вами в ближайшее время.')
            return redirect('others:articles-list')
    else:
        form = ArticleProposalForm()

    return render(request, 'others/propose_article.html', {
        'form': form,
        'admin_email': getattr(settings, 'ADMIN_CONTACT_EMAIL', 'recipes@example.com')
    })


@user_passes_test(lambda u: u.is_staff)
def article_proposals_list(request):
    """Список предложений статей для админов"""
    proposals = ArticleProposal.objects.all().order_by('-created_at')
    pending_proposals = proposals.filter(status='pending')

    context = {
        'proposals': proposals,
        'pending_proposals': pending_proposals,
    }
    return render(request, 'others/article_proposals_list.html', context)


@user_passes_test(lambda u: u.is_staff)
def review_article_proposal(request, pk):
    """Просмотр и решение по предложению статьи"""
    proposal = get_object_or_404(ArticleProposal, pk=pk)

    if request.method == 'POST':
        form = ArticleProposalReviewForm(request.POST, instance=proposal)
        if form.is_valid():
            proposal = form.save(commit=False)
            proposal.reviewed_by = request.user
            proposal.reviewed_at = timezone.now()
            proposal.save()

            messages.success(request, f'Предложение "{proposal.title}" рассмотрено.')
            return redirect('others:article-proposals-list')
    else:
        form = ArticleProposalReviewForm(instance=proposal)

    context = {
        'proposal': proposal,
        'form': form,
    }
    return render(request, 'others/review_article_proposal.html', context)


@user_passes_test(lambda u: u.is_staff)
def create_article_from_proposal(request, pk):
    """Создание статьи на основе предложения"""
    proposal = get_object_or_404(ArticleProposal, pk=pk)

    if request.method == 'POST':
        article_form = ArticleForm(request.POST, request.FILES)
        if article_form.is_valid():
            article = article_form.save(commit=False)
            article.author = request.user
            article.suggested_by = None  # Можно сохранить связь, если есть пользователь
            article.status = 'published'
            article.save()
            article_form.save_m2m()

            # Помечаем предложение как одобренное
            proposal.status = 'approved'
            proposal.reviewed_by = request.user
            proposal.reviewed_at = timezone.now()
            proposal.admin_notes = f'На основе этого предложения создана статья: {article.title}'
            proposal.save()

            messages.success(request, 'Статья успешно создана на основе предложения!')
            return redirect('others:article-detail', pk=article.pk)
    else:
        # Предзаполняем форму данными из предложения
        initial_data = {
            'title': proposal.title,
            'content': proposal.content,
        }
        article_form = ArticleForm(initial=initial_data)

    context = {
        'proposal': proposal,
        'article_form': article_form,
    }
    return render(request, 'others/create_article_from_proposal.html', context)


@login_required
def recommendations_list(request):
    """Страница с рекомендациями для пользователя"""
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