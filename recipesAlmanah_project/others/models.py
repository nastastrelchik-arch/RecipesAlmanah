# others/models.py
from django.db import models
from django.contrib.auth.models import User
from recipes.models import Hashtag


class Article(models.Model):
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    content = models.TextField(verbose_name="Содержание")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор", related_name='articles')
    published_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата публикации")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    hashtags = models.ManyToManyField(Hashtag, blank=True, verbose_name="Хештеги", related_name='articles')
    main_image = models.ImageField(upload_to='articles/images/', blank=True, null=True,
                                   verbose_name="Главное изображение")
    is_published = models.BooleanField(default=True, verbose_name="Опубликовано")
    views_count = models.PositiveIntegerField(default=0, verbose_name="Количество просмотров")

    class Meta:
        verbose_name = "Статья"
        verbose_name_plural = "Статьи"
        ordering = ['-published_at']

    def __str__(self):
        return self.title


class Recommendation(models.Model):
    RECOMMENDATION_TYPES = [
        ('recipe', 'Рецепт'),
        ('article', 'Статья'),
        ('tip', 'Совет'),
        ('technique', 'Техника приготовления'),
    ]

    title = models.CharField(max_length=200, verbose_name="Заголовок")
    content = models.TextField(verbose_name="Содержание")
    recommendation_type = models.CharField(max_length=20, choices=RECOMMENDATION_TYPES, verbose_name="Тип рекомендации")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор", related_name='recommendations')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    related_recipe = models.ForeignKey('recipes.Recipe', on_delete=models.SET_NULL, blank=True, null=True,
                                       verbose_name="Связанный рецепт")
    related_article = models.ForeignKey('Article', on_delete=models.SET_NULL, blank=True, null=True,
                                        verbose_name="Связанная статья")
    is_active = models.BooleanField(default=True, verbose_name="Активно")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок отображения")

    class Meta:
        verbose_name = "Рекомендация"
        verbose_name_plural = "Рекомендации"
        ordering = ['order', '-created_at']

    def __str__(self):
        return f"{self.get_recommendation_type_display()}: {self.title}"


class Statistic(models.Model):
    STATISTIC_TYPES = [
        ('daily_visitors', 'Ежедневные посетители'),
        ('popular_recipes', 'Популярные рецепты'),
        ('user_activity', 'Активность пользователей'),
        ('search_queries', 'Поисковые запросы'),
    ]

    statistic_type = models.CharField(max_length=50, choices=STATISTIC_TYPES, verbose_name="Тип статистики")
    data = models.JSONField(verbose_name="Данные статистики")
    period_start = models.DateField(verbose_name="Начало периода")
    period_end = models.DateField(verbose_name="Конец периода")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Статистика"
        verbose_name_plural = "Статистика"
        ordering = ['-period_end', '-created_at']

    def __str__(self):
        return f"{self.get_statistic_type_display()} ({self.period_start} - {self.period_end})"