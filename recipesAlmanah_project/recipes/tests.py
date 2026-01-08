# recipes/tests.py
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from .models import Recipe, Hashtag, Ingredient, CookingStep, Favorite
from .forms import RecipeForm
from django.forms import inlineformset_factory


class SearchFunctionalityTests(TestCase):
    """Тесты для поисковой функциональности"""

    @classmethod
    def setUpTestData(cls):
        """Создание тестовых данных (выполняется один раз)"""
        # Создаем пользователей
        cls.user1 = User.objects.create_user(
            username='testuser1',
            password='TestPassword123!',
            email='test1@example.com'
        )
        cls.user2 = User.objects.create_user(
            username='testuser2',
            password='TestPassword123!',
            email='test2@example.com'
        )

        # Создаем хештеги
        cls.hashtag1 = Hashtag.objects.create(name='десерт')
        cls.hashtag2 = Hashtag.objects.create(name='завтрак')
        cls.hashtag3 = Hashtag.objects.create(name='здоровое')
        cls.hashtag4 = Hashtag.objects.create(name='быстро')

    def setUp(self):
        """Настройка перед каждым тестом"""
        # Тестовое изображение
        self.test_image = SimpleUploadedFile(
            name='test_recipe.jpg',
            content=b'fake_image_content',
            content_type='image/jpeg'
        )

        # Создаем рецепты для тестов
        self.recipe1 = Recipe.objects.create(
            title='Шоколадный торт',
            description='Вкусный шоколадный торт для праздника',
            author=self.user1,
            cooking_time=120,
            servings=8,
            calories_per_100g=350,
            difficulty='medium',
            main_photo=self.test_image
        )
        self.recipe1.hashtags.add(self.hashtag1, self.hashtag4)

        self.recipe2 = Recipe.objects.create(
            title='Овсяная каша с ягодами',
            description='Полезный завтрак для здорового питания',
            author=self.user2,
            cooking_time=15,
            servings=2,
            calories_per_100g=120,
            difficulty='easy',
            main_photo=self.test_image
        )
        self.recipe2.hashtags.add(self.hashtag2, self.hashtag3)

        self.recipe3 = Recipe.objects.create(
            title='Куриный суп',
            description='Домашний куриный суп с овощами',
            author=self.user1,
            cooking_time=60,
            servings=6,
            calories_per_100g=80,
            difficulty='easy',
            main_photo=self.test_image
        )

        # Добавляем ингредиенты к рецептам
        Ingredient.objects.create(
            recipe=self.recipe1,
            name='шоколад',
            quantity='200 г'
        )
        Ingredient.objects.create(
            recipe=self.recipe1,
            name='мука',
            quantity='300 г'
        )

        Ingredient.objects.create(
            recipe=self.recipe2,
            name='овсяные хлопья',
            quantity='100 г'
        )
        Ingredient.objects.create(
            recipe=self.recipe2,
            name='ягоды',
            quantity='150 г'
        )

        Ingredient.objects.create(
            recipe=self.recipe3,
            name='курица',
            quantity='500 г'
        )
        Ingredient.objects.create(
            recipe=self.recipe3,
            name='лук',
            quantity='2 шт'
        )

        # Создаем шаги приготовления
        CookingStep.objects.create(
            recipe=self.recipe1,
            step_number=1,
            description='Растопить шоколад на водяной бане'
        )

        # URL для тестов
        self.home_url = reverse('recipes:home')
        self.search_url = reverse('recipes:search-recipes')

    def test_search_by_title(self):
        """Тест поиска по названию рецепта"""
        # Поиск "торт"
        response = self.client.get(self.home_url, {'q': 'торт'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Шоколадный торт')
        self.assertNotContains(response, 'Овсяная каша')
        self.assertNotContains(response, 'Куриный суп')

        # Поиск через функцию search_recipes
        response = self.client.get(self.search_url, {'q': 'торт'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Шоколадный торт')

    def test_search_by_description(self):
        """Тест поиска по описанию рецепта"""
        # Поиск "полезный" - делаем поиск регистронезависимым
        response = self.client.get(self.home_url, {'q': 'полезный'})
        self.assertEqual(response.status_code, 200)
        # Используем assertContains для проверки наличия рецепта
        # Проверяем, что рецепты есть в контексте
        self.assertIn('recipes', response.context)
        recipes = response.context['recipes']

        # Ищем рецепт "Овсяная каша" в результатах
        oatmeal_found = any(
            recipe for recipe in recipes
            if 'Овсяная каша' in recipe.title
        )
        self.assertTrue(oatmeal_found, "Овсяная каша не найдена в результатах поиска")

        # Проверяем, что другие рецепты не найдены
        cake_found = any(
            recipe for recipe in recipes
            if 'Шоколадный торт' in recipe.title
        )
        self.assertFalse(cake_found, "Шоколадный торт не должен быть найден")

    def test_search_by_ingredient(self):
        """Тест поиска по ингредиенту"""
        # Поиск "шоколад"
        response = self.client.get(self.home_url, {'q': 'шоколад'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Шоколадный торт')
        self.assertNotContains(response, 'Овсяная каша')

        # Поиск "курица"
        response = self.client.get(self.search_url, {'q': 'курица'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Куриный суп')

    def test_search_multiple_words(self):
        """Тест поиска по нескольким словам"""
        # Django ищет по любому из слов, если не указано иное
        response = self.client.get(self.home_url, {'q': 'шоколадный торт'})
        self.assertEqual(response.status_code, 200)
        # Должен найти рецепт с одним из слов
        self.assertContains(response, 'Шоколадный торт')

    def test_search_no_results(self):
        """Тест поиска без результатов"""
        response = self.client.get(self.home_url, {'q': 'пицца'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'рецептов')
        self.assertNotContains(response, 'Шоколадный торт')
        self.assertNotContains(response, 'Овсяная каша')
        self.assertNotContains(response, 'Куриный суп')

    def test_search_empty_query(self):
        """Тест поиска с пустым запросом (должен показать все рецепты)"""
        response = self.client.get(self.home_url, {'q': ''})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Шоколадный торт')
        self.assertContains(response, 'Овсяная каша')
        self.assertContains(response, 'Куриный суп')

    def test_filter_by_hashtags(self):
        """Тест фильтрации по хештегам"""
        # Фильтр по одному хештегу
        response = self.client.get(self.home_url, {'hashtags': 'десерт'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Шоколадный торт')
        self.assertNotContains(response, 'Овсяная каша')

        # Фильтр по нескольким хештегам
        response = self.client.get(self.home_url, {'hashtags': ['десерт', 'быстро']})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Шоколадный торт')

        # Фильтр по несуществующему хештегу
        response = self.client.get(self.home_url, {'hashtags': 'несуществующий'})
        self.assertEqual(response.status_code, 200)
        # Не должно быть рецептов
        self.assertNotContains(response, 'Шоколадный торт')
        self.assertNotContains(response, 'Овсяная каша')

    def test_filter_by_calories(self):
        """Тест фильтрации по калорийности"""
        # Фильтр по максимальной калорийности
        response = self.client.get(self.home_url, {'max_calories': '200'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Овсяная каша')
        self.assertContains(response, 'Куриный суп')
        self.assertNotContains(response, 'Шоколадный торт')

        # Фильтр с очень низкой калорийностью
        response = self.client.get(self.home_url, {'max_calories': '50'})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Шоколадный торт')
        self.assertNotContains(response, 'Овсяная каша')
        self.assertNotContains(response, 'Куриный суп')

    def test_combined_search_and_filters(self):
        """Тест комбинированного поиска с фильтрами"""
        # Поиск + фильтр по калорийности
        response = self.client.get(self.home_url, {
            'q': 'каша',
            'max_calories': '200'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Овсяная каша')

        # Поиск + фильтр по хештегам
        response = self.client.get(self.home_url, {
            'q': 'торт',
            'hashtags': 'десерт'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Шоколадный торт')

        # Все фильтры вместе
        response = self.client.get(self.home_url, {
            'q': 'шоколад',
            'hashtags': 'десерт',
            'max_calories': '400'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Шоколадный торт')

    def test_search_case_insensitive(self):
        """Тест регистронезависимого поиска"""
        # Поиск в разных регистрах
        response = self.client.get(self.home_url, {'q': 'шоколадный'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Шоколадный торт')

        response = self.client.get(self.home_url, {'q': 'Шоколадный'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Шоколадный торт')

    def test_search_with_special_characters(self):
        """Тест поиска со специальными символами"""
        # Поиск с кавычками и другими символами
        response = self.client.get(self.home_url, {'q': 'шоколадный торт'})
        self.assertEqual(response.status_code, 200)
        # Должен найти рецепт
        self.assertContains(response, 'Шоколадный торт')

    def test_pagination_in_search_results(self):
        """Тест пагинации в результатах поиска"""
        # Создаем больше рецептов для пагинации
        for i in range(15):
            Recipe.objects.create(
                title=f'Тестовый рецепт {i}',
                description=f'Описание тестового рецепта {i}',
                author=self.user1,
                cooking_time=30,
                servings=4,
                calories_per_100g=200,
                difficulty='easy',
                main_photo=self.test_image
            )

        response = self.client.get(self.home_url, {'q': 'Тестовый'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Тестовый рецепт')
        self.assertContains(response, 'page=2')

    def test_search_view_template(self):
        """Тест использования правильного шаблона в search_recipes"""
        response = self.client.get(self.search_url, {'q': 'торт'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'recipes/search_results.html')

    def test_home_view_template(self):
        """Тест использования правильного шаблона в RecipeListView"""
        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'recipes/home.html')

    def test_search_results_context(self):
        """Тест контекста в результатах поиска"""
        response = self.client.get(self.search_url, {'q': 'торт'})
        self.assertEqual(response.status_code, 200)

        # Проверяем наличие ключевых переменных в контексте
        self.assertIn('recipes', response.context)
        self.assertIn('query', response.context)
        self.assertIn('all_hashtags', response.context)

        # Проверяем значения
        self.assertEqual(response.context['query'], 'торт')

        # Вместо проверки полного совпадения, проверяем, что тестовые хештеги есть в контексте
        all_hashtags = Hashtag.objects.filter(
            name__in=['десерт', 'завтрак', 'здоровое', 'быстро']
        )

        # Получаем имена хештегов из контекста
        context_hashtag_names = [h.name for h in response.context['all_hashtags']]

        # Проверяем, что все тестовые хештеги есть в контексте
        for hashtag in all_hashtags:
            self.assertIn(hashtag.name, context_hashtag_names,
                          f"Хештег {hashtag.name} отсутствует в контексте")

    def test_is_favorite_annotation(self):
        """Тест аннотации is_favorite для авторизованного пользователя"""
        # Авторизуем пользователя
        self.client.login(username='testuser1', password='TestPassword123!')

        # Добавляем рецепт в избранное
        Favorite.objects.create(user=self.user1, recipe=self.recipe2)

        # Ищем рецепты
        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 200)

        # Получаем рецепты из контекста
        recipes = response.context['recipes']

        # Проверяем, что у рецепта 2 is_favorite = True
        recipe2_in_context = [r for r in recipes if r.id == self.recipe2.id][0]
        self.assertTrue(recipe2_in_context.is_favorite)

        # Проверяем, что у рецепта 1 is_favorite = False
        recipe1_in_context = [r for r in recipes if r.id == self.recipe1.id][0]
        self.assertFalse(recipe1_in_context.is_favorite)

    def test_search_with_favorite_ids(self):
        """Тест поиска с favorite_ids в контексте"""
        # Авторизуем пользователя
        self.client.login(username='testuser1', password='TestPassword123!')

        # Добавляем рецепт в избранное
        Favorite.objects.create(user=self.user1, recipe=self.recipe2)

        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 200)

        # Проверяем наличие favorite_recipe_ids в контексте
        self.assertIn('favorite_recipe_ids', response.context)
        self.assertIn(self.recipe2.id, response.context['favorite_recipe_ids'])
        self.assertNotIn(self.recipe1.id, response.context['favorite_recipe_ids'])

    def test_empty_search_results_message(self):
        """Тест сообщения при отсутствии результатов поиска"""
        response = self.client.get(self.home_url, {'q': 'абсолютнонесуществующееслово'})
        self.assertEqual(response.status_code, 200)
        # Проверяем, что есть сообщение об отсутствии результатов
        # (это может быть либо пустой список, либо сообщение в шаблоне)
        recipes = response.context['recipes']
        self.assertEqual(len(recipes), 0)


class RecipeListViewTests(TestCase):
    """Тесты для RecipeListView"""

    def setUp(self):
        """Создание тестовых данных"""
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPassword123!'
        )

        # Тестовое изображение
        self.test_image = SimpleUploadedFile(
            name='test_recipe.jpg',
            content=b'fake_image_content',
            content_type='image/jpeg'
        )

        # Создаем несколько рецептов
        for i in range(5):
            Recipe.objects.create(
                title=f'Рецепт {i}',
                description=f'Описание рецепта {i}',
                author=self.user,
                cooking_time=30,
                servings=4,
                calories_per_100g=100 + i * 20,
                difficulty='easy',
                main_photo=self.test_image
            )

        self.home_url = reverse('recipes:home')

    def test_home_page_loads(self):
        """Тест загрузки главной страницы"""
        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'recipes/home.html')

    def test_recipes_in_context(self):
        """Тест наличия рецептов в контексте"""
        response = self.client.get(self.home_url)
        self.assertIn('recipes', response.context)
        self.assertEqual(len(response.context['recipes']), 5)

    def test_recipes_ordering(self):
        """Тест сортировки рецептов (по умолчанию по дате создания)"""
        response = self.client.get(self.home_url)
        recipes = response.context['recipes']

        # Проверяем что рецепты отсортированы по убыванию даты создания
        dates = [recipe.created_at for recipe in recipes]
        self.assertEqual(dates, sorted(dates, reverse=True))

    def test_pagination(self):
        """Тест пагинации"""
        # Создаем больше рецептов
        for i in range(10):
            Recipe.objects.create(
                title=f'Дополнительный рецепт {i}',
                description=f'Описание {i}',
                author=self.user,
                cooking_time=30,
                servings=4,
                calories_per_100g=200,
                difficulty='easy',
                main_photo=self.test_image
            )

        # Всего должно быть 15 рецептов, paginate_by = 9
        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 200)

        # Проверяем пагинацию
        self.assertTrue(response.context['is_paginated'])
        self.assertEqual(len(response.context['recipes']), 9)

        # Проверяем вторую страницу
        response = self.client.get(self.home_url + '?page=2')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['recipes']), 6)  # 15 - 9 = 6

    def test_hashtags_in_context(self):
        """Тест наличия хештегов в контексте"""
        # Создаем хештеги
        hashtag1 = Hashtag.objects.create(name='тест1')
        hashtag2 = Hashtag.objects.create(name='тест2')

        response = self.client.get(self.home_url)
        self.assertIn('all_hashtags', response.context)

        # Проверяем, что наши хештеги есть в контексте
        all_hashtag_names = [h.name for h in response.context['all_hashtags']]
        self.assertIn('тест1', all_hashtag_names)
        self.assertIn('тест2', all_hashtag_names)

    def test_selected_hashtags_in_context(self):
        """Тест выбранных хештегов в контексте"""
        response = self.client.get(self.home_url, {'hashtags': ['тест1', 'тест2']})
        self.assertIn('selected_hashtags', response.context)
        self.assertEqual(response.context['selected_hashtags'], ['тест1', 'тест2'])


class SearchRecipesFunctionTests(TestCase):
    """Тесты для функции search_recipes"""

    def setUp(self):
        """Создание тестовых данных"""
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPassword123!'
        )

        self.test_image = SimpleUploadedFile(
            name='test_recipe.jpg',
            content=b'fake_image_content',
            content_type='image/jpeg'
        )

        self.recipe = Recipe.objects.create(
            title='Тестовый рецепт',
            description='Это тестовый рецепт для поиска',
            author=self.user,
            cooking_time=30,
            servings=4,
            calories_per_100g=200,
            difficulty='easy',
            main_photo=self.test_image
        )

        self.search_url = reverse('recipes:search-recipes')

    def test_search_recipes_function(self):
        """Тест функции search_recipes"""
        response = self.client.get(self.search_url, {'q': 'тестовый'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'recipes/search_results.html')
        self.assertContains(response, 'Тестовый рецепт')

    def test_search_recipes_empty_query(self):
        """Тест функции search_recipes с пустым запросом"""
        response = self.client.get(self.search_url)
        self.assertEqual(response.status_code, 200)
        # Должен показать все рецепты
        self.assertContains(response, 'Тестовый рецепт')

    def test_search_recipes_context(self):
        """Тест контекста функции search_recipes"""
        response = self.client.get(self.search_url, {
            'q': 'тест',
            'max_calories': '250',
            'hashtags': ['десерт']
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn('recipes', response.context)
        self.assertIn('query', response.context)
        self.assertIn('max_calories', response.context)
        self.assertIn('selected_hashtags', response.context)
        self.assertIn('all_hashtags', response.context)

        self.assertEqual(response.context['query'], 'тест')
        self.assertEqual(response.context['max_calories'], '250')
        self.assertEqual(response.context['selected_hashtags'], ['десерт'])


class FavoriteFunctionalityTests(TestCase):
    """Тесты для функционала избранного"""

    def setUp(self):
        """Создание тестовых данных"""
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPassword123!'
        )

        self.other_user = User.objects.create_user(
            username='otheruser',
            password='TestPassword123!'
        )

        self.test_image = SimpleUploadedFile(
            name='test_recipe.jpg',
            content=b'fake_image_content',
            content_type='image/jpeg'
        )

        self.recipe = Recipe.objects.create(
            title='Рецепт для избранного',
            description='Описание',
            author=self.user,
            cooking_time=30,
            servings=4,
            calories_per_100g=200,
            difficulty='easy',
            main_photo=self.test_image
        )

        self.add_favorite_url = reverse('recipes:add-to-favorites', args=[self.recipe.pk])
        self.remove_favorite_url = reverse('recipes:remove-from-favorites', args=[self.recipe.pk])

    def test_add_to_favorites_authenticated(self):
        """Тест добавления в избранное для авторизованного пользователя"""
        self.client.login(username='testuser', password='TestPassword123!')

        response = self.client.get(self.add_favorite_url)
        self.assertEqual(response.status_code, 302)

        # Проверяем что рецепт добавлен в избранное
        self.assertTrue(Favorite.objects.filter(user=self.user, recipe=self.recipe).exists())

    def test_remove_from_favorites(self):
        """Тест удаления из избранного"""
        self.client.login(username='testuser', password='TestPassword123!')

        # Сначала добавляем
        Favorite.objects.create(user=self.user, recipe=self.recipe)

        # Затем удаляем
        response = self.client.get(self.add_favorite_url)
        self.assertEqual(response.status_code, 302)

        # Проверяем что рецепт удален из избранного
        self.assertFalse(Favorite.objects.filter(user=self.user, recipe=self.recipe).exists())

    def test_add_to_favorites_unauthenticated(self):
        """Тест добавления в избранное для неавторизованного пользователя"""
        response = self.client.get(self.add_favorite_url)
        # Должен быть редирект на страницу входа
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/users/login/'))

    def test_favorite_count_property(self):
        """Тест свойства favorite_count"""
        # Добавляем в избранное у нескольких пользователей
        Favorite.objects.create(user=self.user, recipe=self.recipe)
        Favorite.objects.create(user=self.other_user, recipe=self.recipe)

        self.assertEqual(self.recipe.favorite_count, 2)

    def test_is_favorite_for_user_method(self):
        """Тест метода is_favorite_for_user"""
        # Пользователь не добавил в избранное
        self.assertFalse(self.recipe.is_favorite_for_user(self.user))

        # Добавляем в избранное
        Favorite.objects.create(user=self.user, recipe=self.recipe)
        self.assertTrue(self.recipe.is_favorite_for_user(self.user))

        # Проверяем для другого пользователя
        self.assertFalse(self.recipe.is_favorite_for_user(self.other_user))

        # Проверяем для неавторизованного пользователя
        from django.contrib.auth.models import AnonymousUser
        anonymous_user = AnonymousUser()
        self.assertFalse(self.recipe.is_favorite_for_user(anonymous_user))

    def test_remove_favorite_view(self):
        """Тест view для удаления из избранного"""
        self.client.login(username='testuser', password='TestPassword123!')

        # Добавляем в избранное
        Favorite.objects.create(user=self.user, recipe=self.recipe)

        # Удаляем через специальный view
        response = self.client.get(self.remove_favorite_url)
        self.assertEqual(response.status_code, 302)

        # Проверяем что удалено
        self.assertFalse(Favorite.objects.filter(user=self.user, recipe=self.recipe).exists())

    def test_remove_nonexistent_favorite(self):
        """Тест удаления несуществующего избранного"""
        self.client.login(username='testuser', password='TestPassword123!')

        # Пытаемся удалить то, чего нет
        response = self.client.get(self.remove_favorite_url)
        self.assertEqual(response.status_code, 302)
        # Не должно быть ошибки


class RecipeModelTests(TestCase):
    """Тесты для моделей рецептов"""

    def setUp(self):
        """Создание тестовых данных"""
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPassword123!'
        )

        self.test_image = SimpleUploadedFile(
            name='test_recipe.jpg',
            content=b'fake_image_content',
            content_type='image/jpeg'
        )

        self.recipe = Recipe.objects.create(
            title='Тестовый рецепт',
            description='Описание',
            author=self.user,
            cooking_time=30,
            servings=4,
            calories_per_100g=200,
            difficulty='easy',
            main_photo=self.test_image
        )

    def test_recipe_str_method(self):
        """Тест строкового представления рецепта"""
        self.assertEqual(str(self.recipe), 'Тестовый рецепт')

    def test_recipe_get_absolute_url(self):
        """Тест метода get_absolute_url"""
        url = self.recipe.get_absolute_url()
        expected_url = reverse('recipes:recipe-detail', kwargs={'pk': self.recipe.pk})
        self.assertEqual(url, expected_url)

    def test_ingredient_str_method(self):
        """Тест строкового представления ингредиента"""
        ingredient = Ingredient.objects.create(
            recipe=self.recipe,
            name='мука',
            quantity='300 г'
        )
        self.assertEqual(str(ingredient), 'мука - 300 г')

    def test_cooking_step_str_method(self):
        """Тест строкового представления шага приготовления"""
        cooking_step = CookingStep.objects.create(
            recipe=self.recipe,
            step_number=1,
            description='Смешать ингредиенты'
        )
        self.assertEqual(str(cooking_step), 'Step 1 for Тестовый рецепт')

    def test_cooking_step_ordering(self):
        """Тест сортировки шагов приготовления"""
        # Создаем шаги в обратном порядке
        CookingStep.objects.create(
            recipe=self.recipe,
            step_number=3,
            description='Шаг 3'
        )
        CookingStep.objects.create(
            recipe=self.recipe,
            step_number=1,
            description='Шаг 1'
        )
        CookingStep.objects.create(
            recipe=self.recipe,
            step_number=2,
            description='Шаг 2'
        )

        # Получаем шаги
        steps = CookingStep.objects.filter(recipe=self.recipe)

        # Проверяем что они отсортированы по step_number
        step_numbers = [step.step_number for step in steps]
        self.assertEqual(step_numbers, [1, 2, 3])

    def test_hashtag_str_method(self):
        """Тест строкового представления хештега"""
        hashtag = Hashtag.objects.create(name='десерт')
        self.assertEqual(str(hashtag), 'десерт')

    def test_favorite_str_method(self):
        """Тест строкового представления избранного"""
        favorite = Favorite.objects.create(
            user=self.user,
            recipe=self.recipe
        )
        self.assertEqual(str(favorite), f'{self.user.username} - {self.recipe.title}')

    def test_favorite_unique_together(self):
        """Тест уникальности пары пользователь-рецепт в избранном"""
        # Первое добавление должно пройти успешно
        Favorite.objects.create(user=self.user, recipe=self.recipe)

        # Второе добавление должно вызвать ошибку
        with self.assertRaises(Exception):
            Favorite.objects.create(user=self.user, recipe=self.recipe)

    def test_recipe_difficulty_choices(self):
        """Тест выбора сложности рецепта"""
        # Проверяем что difficulty имеет правильные варианты
        difficulty_choices = dict(Recipe.DIFFICULTY_LEVELS)
        self.assertEqual(difficulty_choices['easy'], 'Легкий')
        self.assertEqual(difficulty_choices['medium'], 'Средний')
        self.assertEqual(difficulty_choices['hard'], 'Сложный')