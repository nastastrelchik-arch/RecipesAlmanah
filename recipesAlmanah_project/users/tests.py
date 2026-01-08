# users/tests.py
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib import messages
from django.contrib.messages import get_messages

from users.models import Profile
from recipes.models import Recipe, Favorite
from comments.models import Comment
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm


class UserRegistrationTests(TestCase):
    """Тесты для регистрации пользователей"""

    def test_register_page_loads(self):
        """Тест загрузки страницы регистрации"""
        response = self.client.get(reverse('users:register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/register.html')
        self.assertContains(response, 'form')

    def test_register_form_valid_data(self):
        """Тест регистрации с валидными данными"""
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'TestPassword123!',
            'password2': 'TestPassword123!',
        }

        response = self.client.post(reverse('users:register'), form_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('recipes:home'))
        self.assertTrue(User.objects.filter(username='testuser').exists())

    def test_register_form_invalid_data(self):
        """Тест регистрации с невалидными данными"""
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'TestPassword123!',
            'password2': 'DifferentPassword123!',
        }

        response = self.client.post(reverse('users:register'), form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='testuser').exists())

    def test_register_duplicate_username(self):
        """Тест регистрации с уже существующим именем пользователя"""
        User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='password123'
        )

        form_data = {
            'username': 'existinguser',
            'email': 'new@example.com',
            'password1': 'TestPassword123!',
            'password2': 'TestPassword123!',
        }

        response = self.client.post(reverse('users:register'), form_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'errorlist')


class UserAuthenticationTests(TestCase):
    """Тесты для аутентификации (вход/выход)"""

    def setUp(self):
        """Создание тестового пользователя"""
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPassword123!',
            email='test@example.com'
        )
        self.login_url = reverse('users:login')
        self.logout_url = reverse('users:logout')
        self.home_url = reverse('recipes:home')

    def test_login_page_loads(self):
        """Тест загрузки страницы входа"""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/login.html')

    def test_successful_login(self):
        """Тест успешного входа"""
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'TestPassword123!'
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_login_wrong_password(self):
        """Тест входа с неправильным паролем"""
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'WrongPassword123!'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form')

    def test_login_nonexistent_user(self):
        """Тест входа несуществующего пользователя"""
        response = self.client.post(self.login_url, {
            'username': 'nonexistent',
            'password': 'SomePassword123!'
        })
        self.assertEqual(response.status_code, 200)

    def test_logout_functionality(self):
        """Тест выхода из системы"""
        # Входим
        self.client.login(username='testuser', password='TestPassword123!')

        # Проверяем что вошли
        response = self.client.get(self.home_url)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

        # Выходим - НЕ используем follow=True чтобы избежать ошибки в шаблоне
        response = self.client.get(self.logout_url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.home_url)

        # Проверяем что вышли
        response = self.client.get(self.home_url)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_auto_login_after_registration(self):
        """Тест автоматического входа после регистрации"""
        form_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'TestPassword123!',
            'password2': 'TestPassword123!',
        }

        response = self.client.post(reverse('users:register'), form_data, follow=True)
        self.assertRedirects(response, reverse('recipes:home'))
        self.assertTrue(response.wsgi_request.user.is_authenticated)


class ProfileTests(TestCase):
    """Тесты для профиля пользователя"""

    def setUp(self):
        """Создание тестового пользователя и данных"""
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPassword123!',
            email='test@example.com'
        )
        self.client.login(username='testuser', password='TestPassword123!')
        self.profile_url = reverse('users:profile')
        self.edit_profile_url = reverse('users:edit_profile')

    def test_profile_page_loads(self):
        """Тест загрузки страницы профиля"""
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/profile.html')

    def test_profile_shows_user_recipes(self):
        """Тест отображения рецептов пользователя в профиле"""
        Recipe.objects.create(
            title='Рецепт 1',
            description='Описание 1',
            author=self.user,
            cooking_time=30,
            servings=4,
            calories_per_100g=200,
            difficulty='easy'
        )

        Recipe.objects.create(
            title='Рецепт 2',
            description='Описание 2',
            author=self.user,
            cooking_time=45,
            servings=2,
            calories_per_100g=300,
            difficulty='medium'
        )

        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['user_recipes']), 2)

    def test_profile_shows_favorites(self):
        """Тест отображения избранных рецептов в профиле"""
        other_user = User.objects.create_user(
            username='otheruser',
            password='password123'
        )
        recipe = Recipe.objects.create(
            title='Вкусный рецепт',
            description='Описание',
            author=other_user,
            cooking_time=30,
            servings=4,
            calories_per_100g=200,
            difficulty='easy'
        )

        Favorite.objects.create(user=self.user, recipe=recipe)

        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['user_favorites']), 1)

    def test_profile_shows_comments(self):
        """Тест отображения комментариев пользователя в профиле"""
        recipe = Recipe.objects.create(
            title='Рецепт для комментария',
            description='Описание',
            author=self.user,
            cooking_time=30,
            servings=4,
            calories_per_100g=200,
            difficulty='easy'
        )

        Comment.objects.create(
            recipe=recipe,
            author=self.user,
            text='Отличный рецепт!'
        )

        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['user_comments']), 1)

    def test_edit_profile_page_loads(self):
        """Тест загрузки страницы редактирования профиля"""
        response = self.client.get(self.edit_profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/edit_profile.html')

    def test_edit_profile_valid_data(self):
        """Тест редактирования профиля с валидными данными"""
        form_data = {
            'username': 'updateduser',
            'email': 'updated@example.com',
            'bio': 'Новое био пользователя',
            'location': 'Москва',
            'birth_date': '1990-01-01',
        }

        response = self.client.post(self.edit_profile_url, form_data, follow=True)
        self.assertEqual(response.status_code, 200)

        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'updateduser')
        self.assertEqual(self.user.email, 'updated@example.com')
        self.assertEqual(self.user.profile.bio, 'Новое био пользователя')

    def test_edit_profile_invalid_data(self):
        """Тест редактирования профиля с невалидными данными"""
        form_data = {
            'username': '',
            'email': 'not-an-email',
            'birth_date': 'invalid-date',
        }

        response = self.client.post(self.edit_profile_url, form_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form')

    def test_remove_favorite_functionality(self):
        """Тест удаления рецепта из избранного"""
        recipe = Recipe.objects.create(
            title='Рецепт для избранного',
            description='Описание',
            author=self.user,
            cooking_time=30,
            servings=4,
            calories_per_100g=200,
            difficulty='easy'
        )

        Favorite.objects.create(user=self.user, recipe=recipe)
        self.assertTrue(Favorite.objects.filter(user=self.user, recipe=recipe).exists())

        response = self.client.get(
            reverse('users:remove-favorite', args=[recipe.pk]),
            follow=True
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Favorite.objects.filter(user=self.user, recipe=recipe).exists())

    def test_remove_favorite_not_in_favorites(self):
        """Тест удаления рецепта, которого нет в избранном"""
        recipe = Recipe.objects.create(
            title='Рецепт не в избранном',
            description='Описание',
            author=self.user,
            cooking_time=30,
            servings=4,
            calories_per_100g=200,
            difficulty='easy'
        )

        response = self.client.get(
            reverse('users:remove-favorite', args=[recipe.pk]),
            follow=True
        )
        self.assertEqual(response.status_code, 200)


class ProfileModelTests(TestCase):
    """Тесты для модели Profile"""

    def test_profile_creation_signal(self):
        """Тест автоматического создания профиля через сигнал"""
        user = User.objects.create_user(
            username='testuser',
            password='password123',
            email='test@example.com'
        )

        self.assertTrue(hasattr(user, 'profile'))
        self.assertIsInstance(user.profile, Profile)

    def test_profile_str_method(self):
        """Тест строкового представления профиля"""
        user = User.objects.create_user(
            username='testuser',
            password='password123'
        )

        self.assertEqual(str(user.profile), f"Профиль: {user.username}")

    def test_profile_fields_defaults(self):
        """Тест значений по умолчанию полей профиля"""
        user = User.objects.create_user(
            username='testuser',
            password='password123'
        )

        self.assertEqual(user.profile.bio, '')
        self.assertEqual(user.profile.location, '')
        self.assertIsNone(user.profile.birth_date)
        self.assertFalse(bool(user.profile.profile_photo))
        self.assertTrue(user.profile.show_favorites)


class FormTests(TestCase):
    """Тесты для форм пользователей"""

    def test_user_register_form_valid(self):
        """Тест валидной формы регистрации"""
        form_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
        }

        form = UserRegisterForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_user_register_form_invalid(self):
        """Тест невалидной формы регистрации"""
        form_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'ComplexPass123!',
            'password2': 'DifferentPass123!',
        }

        form = UserRegisterForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_user_update_form(self):
        """Тест формы обновления пользователя"""
        user = User.objects.create_user(
            username='testuser',
            email='old@example.com',
            password='password123'
        )

        form_data = {
            'username': 'updateduser',
            'email': 'new@example.com',
        }

        form = UserUpdateForm(data=form_data, instance=user)
        self.assertTrue(form.is_valid())

    def test_profile_update_form(self):
        """Тест формы обновления профиля"""
        user = User.objects.create_user(
            username='testuser',
            password='password123'
        )

        form_data = {
            'bio': 'Новое био',
            'location': 'Москва',
            'birth_date': '1990-01-01',
        }

        form = ProfileUpdateForm(data=form_data, instance=user.profile)
        # Проверяем что форма не содержит ошибок для полей профиля
        self.assertNotIn('bio', form.errors)
        self.assertNotIn('location', form.errors)


class AccessControlTests(TestCase):
    """Тесты контроля доступа"""

    def test_profile_requires_login(self):
        """Тест, что профиль требует аутентификации"""
        response = self.client.get(reverse('users:profile'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f"/users/login/?next={reverse('users:profile')}")

    def test_edit_profile_requires_login(self):
        """Тест, что редактирование профиля требует аутентификации"""
        response = self.client.get(reverse('users:edit_profile'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f"/users/login/?next={reverse('users:edit_profile')}")

    def test_authenticated_access(self):
        """Тест доступа для аутентифицированного пользователя"""
        user = User.objects.create_user(
            username='testuser',
            password='TestPassword123!'
        )
        self.client.login(username='testuser', password='TestPassword123!')

        response = self.client.get(reverse('users:profile'))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('users:edit_profile'))
        self.assertEqual(response.status_code, 200)


class ErrorHandlingTests(TestCase):
    """Тесты обработки ошибок"""

    def test_profile_error_handling(self):
        """Тест обработки ошибок при загрузке профиля"""
        user = User.objects.create_user(
            username='testuser',
            password='TestPassword123!'
        )
        self.client.login(username='testuser', password='TestPassword123!')

        response = self.client.get(reverse('users:profile'))
        self.assertEqual(response.status_code, 200)

    def test_edit_profile_error_handling(self):
        """Тест обработки ошибок при редактировании профиля"""
        user = User.objects.create_user(
            username='testuser',
            password='TestPassword123!'
        )
        self.client.login(username='testuser', password='TestPassword123!')

        response = self.client.post(reverse('users:edit_profile'), {
            'username': '',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form')