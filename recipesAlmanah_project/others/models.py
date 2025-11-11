from django.db import models
from django.contrib.auth.models import User
from recipes.models import Hashtag, Recipe
from django.core.cache import cache
from django.db.models import Count


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
            cache.set(cache_key, recommendations, 3600)  # Кэшируем на 1 час
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

        # 2. Популярные рецепты
        popular_recipes = self.get_popular_recipes()
        print(f"Популярных рецептов: {len(popular_recipes)}")

        if popular_recipes:
            recommendations.append({
                'type': 'popular',
                'title': 'Популярные рецепты',
                'description': 'Самые популярные рецепты на сайте',
                'recipes': popular_recipes
            })

        # 3. Трендовые рецепты
        trending_recipes = self.get_trending_recipes()
        print(f"Трендовых рецептов: {len(trending_recipes) if trending_recipes else 0}")

        if trending_recipes:
            recommendations.append({
                'type': 'trending',
                'title': 'Сейчас в тренде',
                'description': 'Рецепты с популярными хештегами',
                'recipes': trending_recipes
            })

        print(f"Итого рекомендаций: {len(recommendations)} категорий")
        return recommendations

    def get_recommendations_by_favorite_hashtags(self, user):
        """Рекомендации на основе хештегов из избранных рецептов"""
        print("Поиск рекомендаций по хештегам из избранного...")

        # Получаем избранные рецепты пользователя
        favorite_recipes = user.favorite_set.all()
        print(f"Найдено избранных рецептов: {favorite_recipes.count()}")

        if not favorite_recipes:
            print("Нет избранных рецептов")
            return None

        favorite_recipe_ids = [fav.recipe.id for fav in favorite_recipes]
        print(f"ID избранных рецептов: {favorite_recipe_ids}")

        # Находим популярные хештеги в избранном
        favorite_hashtags = Hashtag.objects.filter(  # Теперь Hashtag импортирован
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
        recommended_recipes = Recipe.objects.filter(  # Recipe тоже импортирован
            hashtags__in=favorite_hashtags
        ).exclude(
            id__in=favorite_recipe_ids
        ).distinct().order_by('-created_at')[:8]

        print(f"Найдено рекомендованных рецептов: {recommended_recipes.count()}")
        for recipe in recommended_recipes:
            print(f" - {recipe.title}: {[tag.name for tag in recipe.hashtags.all()]}")

        return list(recommended_recipes)

    def get_popular_recipes(self):
        """Самые популярные рецепты (по количеству добавлений в избранное)"""
        print("Поиск популярных рецептов...")

        # Используем аннотацию вместо свойства favorite_count
        popular_recipes = Recipe.objects.annotate(
            fav_count=Count('favorite')  # Используем другое имя для аннотации
        ).filter(
            fav_count__gt=0
        ).order_by('-fav_count', '-created_at')[:8]  # Сортируем по аннотации

        print(f"Найдено популярных рецептов: {popular_recipes.count()}")
        for recipe in popular_recipes:
            # Получаем количество избранных через аннотацию
            fav_count = getattr(recipe, 'fav_count', 0)
            print(f" - {recipe.title}: {fav_count} избранных")

        return list(popular_recipes)

    def get_trending_recipes(self):
        """Рецепты с популярными хештегами"""
        print("Поиск трендовых рецептов...")

        # Находим популярные хештеги
        popular_hashtags = Hashtag.objects.annotate(  # Hashtag импортирован
            recipe_count=Count('recipe')
        ).filter(
            recipe_count__gt=0
        ).order_by('-recipe_count')[:3]

        print(f"Найдено популярных хештегов: {popular_hashtags.count()}")
        for hashtag in popular_hashtags:
            print(f" - {hashtag.name}: {hashtag.recipe_count} рецептов")

        if not popular_hashtags:
            print("Нет популярных хештегов")
            return None

        # Ищем рецепты с этими хештегами
        trending_recipes = Recipe.objects.filter(  # Recipe импортирован
            hashtags__in=popular_hashtags
        ).distinct().order_by('-created_at')[:8]

        print(f"Найдено трендовых рецептов: {trending_recipes.count()}")
        for recipe in trending_recipes:
            print(f" - {recipe.title}: {[tag.name for tag in recipe.hashtags.all()]}")

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
    recipes = models.ManyToManyField(Recipe, verbose_name="Рекомендуемые рецепты")  # Recipe импортирован
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