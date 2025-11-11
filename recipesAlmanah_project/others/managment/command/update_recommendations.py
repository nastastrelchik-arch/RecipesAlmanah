from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from others.models import Recommendation


class Command(BaseCommand):
    help = 'Обновить кэш рекомендаций для всех пользователей'

    def handle(self, *args, **options):
        users = User.objects.all()
        for user in users:
            # Генерируем рекомендации для каждого пользователя
            recommendations = Recommendation.generate_recommendations(user)
            self.stdout.write(
                self.style.SUCCESS(f'Обновлены рекомендации для {user.username}: {len(recommendations)} категорий')
            )