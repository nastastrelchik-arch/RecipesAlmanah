from django.urls import path
from . import views

app_name = 'others'

urlpatterns = [
    # Статьи
    path('articles/', views.articles_list, name='articles-list'),
    path('articles/<int:pk>/', views.article_detail, name='article-detail'),
    path('articles/create/', views.create_article, name='create-article'),
    path('articles/<int:pk>/edit/', views.edit_article, name='edit-article'),

    # Рекомендации
    path('recommendations/', views.recommendations_list, name='recommendations-list'),

    # Статистика
    path('statistics/', views.statistics_view, name='statistics'),
    path('statistics/public/', views.public_statistics_view, name='public-statistics'),
    path('statistics/update/', views.update_statistics, name='update-statistics'),
]