from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Article, Recommendation, Statistic
from .forms import ArticleForm, RecommendationForm

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

def recommendations_list(request):
    recommendations = Recommendation.objects.filter(is_active=True).order_by('order', '-created_at')
    return render(request, 'others/recommendations_list.html', {'recommendations': recommendations})

# Проверка для админских функций
def is_staff_user(user):
    return user.is_staff

@user_passes_test(is_staff_user)
def statistics_view(request):
    # Здесь будет логика для отображения статистики
    latest_stats = Statistic.objects.all()[:10]
    return render(request, 'others/statistics.html', {'statistics': latest_stats})