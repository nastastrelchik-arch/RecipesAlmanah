from django.urls import path
from . import views

app_name = 'others'

urlpatterns = [
    # Статьи
    path('articles/', views.articles_list, name='articles-list'),
    path('articles/<int:pk>/', views.article_detail, name='article-detail'),
    path('articles/create/', views.create_article, name='create-article'),
    path('articles/<int:pk>/edit/', views.edit_article, name='edit-article'),
    path('articles/management/', views.article_management, name='article-management'),

    # Удаление изображений статей
    path('articles/images/<int:pk>/delete/', views.delete_article_image, name='delete-article-image'),

    # Предложения статей
    path('articles/propose/', views.propose_article, name='propose-article'),
    path('articles/proposals/', views.article_proposals_list, name='article-proposals-list'),
    path('articles/proposals/<int:pk>/review/', views.review_article_proposal, name='review-article-proposal'),
    path('articles/proposals/<int:pk>/create-article/', views.create_article_from_proposal,
         name='create-article-from-proposal'),

    # Рекомендации
    path('recommendations/', views.recommendations_list, name='recommendations-list'),

    # Статистика
    path('statistics/', views.statistics_view, name='statistics'),
    path('statistics/public/', views.public_statistics_view, name='public-statistics'),
    path('statistics/update/', views.update_statistics, name='update-statistics'),
]