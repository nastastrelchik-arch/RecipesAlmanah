from django.db import models
from django.contrib.auth.models import User
from recipes.models import Hashtag, Recipe
from django.core.cache import cache
from django.db.models import Count, Q
from datetime import datetime, timedelta


class StatisticsManager(models.Manager):
    def get_site_statistics(self):
        """Получить общую статистику сайта"""
        cache_key = "site_statistics"
        statistics = cache.get(cache_key)

        if statistics is None:
            statistics = self._generate_site_statistics()
            cache.set(cache_key, statistics, 300)  # Кэшируем на 5 минут
        return statistics

    def _generate_site_statistics(self):
        """Сгенерировать статистику сайта"""
        # Импортируем здесь, чтобы избежать циклических импортов
        from recipes.models import Favorite

        # Топ-10 популярных рецептов (по количеству в избранном)
        # Используем другое имя для аннотации, чтобы избежать конфликта
        popular_recipes = Recipe.objects.annotate(
            fav_count_annotated=Count('favorite')  # Изменили имя
        ).filter(
            fav_count_annotated__gt=0
        ).order_by('-fav_count_annotated')[:10]

        # Новинки (последние 10 рецептов)
        new_recipes = Recipe.objects.all().order_by('-created_at')[:10]

        # Топ-10 популярных хештегов (по количеству использований в рецептах)
        popular_hashtags = Hashtag.objects.annotate(
            usage_count=Count('recipe')
        ).filter(
            usage_count__gt=0
        ).order_by('-usage_count')[:10]

        # Топ-3 популярных автора (по количеству рецептов и избранного)
        popular_authors = User.objects.annotate(
            recipe_count=Count('recipe'),
            total_favorites=Count('recipe__favorite')
        ).filter(
            recipe_count__gt=0
        ).order_by('-total_favorites', '-recipe_count')[:3]

        # Дополнительная статистика
        total_recipes = Recipe.objects.count()
        total_users = User.objects.count()
        total_favorites = Favorite.objects.count()

        # Статистика за последнюю неделю
        week_ago = datetime.now() - timedelta(days=7)
        new_recipes_week = Recipe.objects.filter(created_at__gte=week_ago).count()
        new_users_week = User.objects.filter(date_joined__gte=week_ago).count()

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

    def get_detailed_statistics(self):
        """Получить детальную статистику для админ-панели"""
        # Импортируем здесь, чтобы избежать циклических импортов
        from recipes.models import Favorite

        # Статистика по месяцам
        from django.db.models.functions import TruncMonth

        monthly_stats = Recipe.objects.annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            count=Count('id')
        ).order_by('-month')[:12]

        # Статистика по активным пользователям
        active_users = User.objects.annotate(
            recipe_count=Count('recipe'),
            favorite_count_annotated=Count('favorite')  # Изменили имя
        ).filter(
            Q(recipe_count__gt=0) | Q(favorite_count_annotated__gt=0)
        ).order_by('-recipe_count', '-favorite_count_annotated')[:10]

        # Самые комментируемые рецепты (если есть модель комментариев)
        try:
            from comments.models import Comment
            most_commented = Recipe.objects.annotate(
                comment_count=Count('comments')
            ).filter(
                comment_count__gt=0
            ).order_by('-comment_count')[:10]
        except:
            most_commented = []

        return {
            'monthly_stats': list(monthly_stats),
            'active_users': list(active_users),
            'most_commented': list(most_commented),
        }


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


class RecommendationManager(models.Manager):
    def get_recommendations_for_user(self, user):
        """Получить рекомендации для пользователя"""
        cache_key = f"user_recommendations_{user.id}"
        recommendations = cache.get(cache_key)

        if recommendations is None:
            print(f"Генерация рекомендаций для пользователя {user.username}")
            recommendations = self.generate_recommendations(user)
            cache.set(cache_key, recommendations, 3600)
            print(f"Сгенерировано рекомендаций: {len(recommendations)}")
        else:
            print(f"Рекомендации загружены из кэша: {len(recommendations)}")

        return recommendations

    def generate_recommendations(self, user):
        """Сгенерировать рекомендации для пользователя"""
        recommendations = []

        print(f"=== ГЕНЕРАЦИЯ РЕКОМЕНДАЦИЙ ДЛЯ {user.username} ===")

        # 1. Рекомендации по хештегам из избранного
        favorite_hashtag_recipes = self.get_recommendations_by_favorite_hashtags(user)
        print(f"Рекомендаций по хештегам: {len(favorite_hashtag_recipes) if favorite_hashtag_recipes else 0}")

        if favorite_hashtag_recipes:
            recommendations.append({
                'type': 'hashtag',
                'title': 'По вашим интересам',
                'description': 'Рецепты, которые могут вам понравиться',
                'recipes': favorite_hashtag_recipes
            })

        # 2. Популярные рецепты (по количеству в избранном)
        popular_recipes = self.get_popular_recipes()
        print(f"Популярных рецептов: {len(popular_recipes)}")

        if popular_recipes:
            recommendations.append({
                'type': 'popular',
                'title': 'Популярные рецепты',
                'description': 'Самые добавляемые в избранное рецепты',
                'recipes': popular_recipes
            })

        # 3. Трендовые рецепты (по популярным хештегам поиска)
        trending_recipes = self.get_trending_recipes()
        print(f"Трендовых рецептов: {len(trending_recipes) if trending_recipes else 0}")

        if trending_recipes:
            recommendations.append({
                'type': 'trending',
                'title': 'Сейчас в тренде',
                'description': 'Рецепты с самыми популярными хештегами поиска',
                'recipes': trending_recipes
            })

        print(f"Итого рекомендаций: {len(recommendations)} категорий")
        return recommendations

    def get_recommendations_by_favorite_hashtags(self, user):
        """Рекомендации на основе хештегов из избранных рецептов"""
        print("Поиск рекомендаций по хештегам из избранного...")

        # Импортируем здесь, чтобы избежать циклических импортов
        from recipes.models import Favorite

        favorite_recipes = user.favorite_set.all()
        print(f"Найдено избранных рецептов: {favorite_recipes.count()}")

        if not favorite_recipes:
            print("Нет избранных рецептов")
            return None

        favorite_recipe_ids = [fav.recipe.id for fav in favorite_recipes]
        print(f"ID избранных рецептов: {favorite_recipe_ids}")

        # Находим популярные хештеги в избранном
        favorite_hashtags = Hashtag.objects.filter(
            recipe__in=favorite_recipe_ids
        ).annotate(
            count=Count('recipe')
        ).order_by('-count')[:5]

        print(f"Найдено хештегов в избранном: {favorite_hashtags.count()}")
        for hashtag in favorite_hashtags:
            print(f" - {hashtag.name}: {hashtag.count} рецептов")

        if not favorite_hashtags:
            print("Нет хештегов в избранных рецептах")
            return None

        # Ищем рецепты с этими хештегами, исключая уже избранные
        recommended_recipes = Recipe.objects.filter(
            hashtags__in=favorite_hashtags
        ).exclude(
            id__in=favorite_recipe_ids
        ).distinct().order_by('-created_at')[:8]

        print(f"Найдено рекомендованных рецептов: {recommended_recipes.count()}")
        return list(recommended_recipes)

    def get_popular_recipes(self):
        """Самые популярные рецепты (по количеству добавлений в избранное)"""
        print("Поиск популярных рецептов по избранному...")

        # Используем то же имя для consistency
        popular_recipes = Recipe.objects.annotate(
            fav_count_annotated=Count('favorite')
        ).filter(
            fav_count_annotated__gt=0
        ).order_by('-fav_count_annotated', '-created_at')[:8]

        print(f"Найдено популярных рецептов: {popular_recipes.count()}")
        for recipe in popular_recipes:
            # Получаем количество избранных через аннотацию
            fav_count = getattr(recipe, 'fav_count_annotated', 0)
            print(f" - {recipe.title}: {fav_count} избранных")

        return list(popular_recipes)

    def get_trending_recipes(self):
        """Трендовые рецепты (по популярным хештегам поиска)"""
        print("Поиск трендовых рецептов по хештегам поиска...")

        try:
            # Используем статистику поиска по хештегам
            trending_hashtags = Hashtag.objects.filter(
                search_stats__search_count__gt=0
            ).annotate(
                search_count=Count('search_stats__search_count')
            ).order_by('-search_stats__search_count', '-search_stats__last_searched')[:3]

            # Если нет данных о поиске, используем популярные хештеги как fallback
            if not trending_hashtags:
                print("Нет данных о поиске, используем популярные хештеги...")
                trending_hashtags = Hashtag.objects.annotate(
                    recipe_count=Count('recipe')
                ).filter(
                    recipe_count__gt=0
                ).order_by('-recipe_count')[:3]

        except Exception as e:
            print(f"Ошибка при получении трендовых хештегов: {e}")
            # Fallback на популярные хештеги
            trending_hashtags = Hashtag.objects.annotate(
                recipe_count=Count('recipe')
            ).filter(
                recipe_count__gt=0
            ).order_by('-recipe_count')[:3]

        print(f"Найдено трендовых хештегов: {trending_hashtags.count()}")
        for hashtag in trending_hashtags:
            print(f" - {hashtag.name}")

        if not trending_hashtags:
            print("Нет трендовых хештегов")
            return None

        # Ищем рецепты с этими хештегами
        trending_recipes = Recipe.objects.filter(
            hashtags__in=trending_hashtags
        ).distinct().order_by('-created_at')[:8]

        print(f"Найдено трендовых рецептов: {trending_recipes.count()}")
        return list(trending_recipes)


class Recommendation(models.Model):
    RECOMMENDATION_TYPES = [
        ('hashtag', 'По хештегам'),
        ('popular', 'Популярное'),
        ('trending', 'Трендовое'),
    ]

    title = models.CharField(max_length=200, verbose_name="Заголовок")
    description = models.TextField(verbose_name="Описание", blank=True)
    recommendation_type = models.CharField(max_length=20, choices=RECOMMENDATION_TYPES, verbose_name="Тип рекомендации")
    recipes = models.ManyToManyField(Recipe, verbose_name="Рекомендуемые рецепты")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    is_active = models.BooleanField(default=True, verbose_name="Активно")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок отображения")

    objects = RecommendationManager()

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
        ('site_overview', 'Обзор сайта'),
    ]

    statistic_type = models.CharField(max_length=50, choices=STATISTIC_TYPES, verbose_name="Тип статистики")
    data = models.JSONField(verbose_name="Данные статистики")
    period_start = models.DateField(verbose_name="Начало периода")
    period_end = models.DateField(verbose_name="Конец периода")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    objects = StatisticsManager()  # Добавляем менеджер

    class Meta:
        verbose_name = "Статистика"
        verbose_name_plural = "Статистика"
        ordering = ['-period_end', '-created_at']

    def __str__(self):
        return f"{self.get_statistic_type_display()} ({self.period_start} - {self.period_end})"

    @classmethod
    def update_site_statistics(cls):
        """Обновить статистику сайта в базе данных"""
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)

        # Получаем текущую статистику
        stats_manager = StatisticsManager()
        site_stats = stats_manager.get_site_statistics()
        detailed_stats = stats_manager.get_detailed_statistics()

        # Сохраняем общую статистику
        cls.objects.update_or_create(
            statistic_type='site_overview',
            period_start=week_ago,
            period_end=today,
            defaults={'data': site_stats}
        )

        # Сохраняем детальную статистику
        cls.objects.update_or_create(
            statistic_type='user_activity',
            period_start=week_ago,
            period_end=today,
            defaults={'data': detailed_stats}
        )


class SearchQuery(models.Model):
    """Модель для отслеживания поисковых запросов пользователей"""
    query = models.CharField(max_length=255, verbose_name="Поисковый запрос")
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True,
                             verbose_name="Пользователь")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата запроса")
    results_count = models.PositiveIntegerField(default=0, verbose_name="Количество результатов")

    class Meta:
        verbose_name = "Поисковый запрос"
        verbose_name_plural = "Поисковые запросы"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.query} ({self.created_at})"


class HashtagSearch(models.Model):
    """Статистика использования хештегов в поиске"""
    hashtag = models.ForeignKey(Hashtag, on_delete=models.CASCADE,
                                verbose_name="Хештег", related_name='search_stats')
    search_count = models.PositiveIntegerField(default=0, verbose_name="Количество поисков")
    last_searched = models.DateTimeField(auto_now=True, verbose_name="Последний поиск")

    class Meta:
        verbose_name = "Статистика хештега в поиске"
        verbose_name_plural = "Статистика хештегов в поиске"

    def __str__(self):
        return f"{self.hashtag.name}: {self.search_count} поисков"