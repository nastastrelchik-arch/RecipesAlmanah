# others/management/commands/clear_recommendations_cache.py
from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Очистить кэш рекомендаций для всех пользователей'

    def handle(self, *args, **options):
        users = User.objects.all()
        for user in users:
            cache_key = f"user_recommendations_{user.id}"
            cache.delete(cache_key)
            self.stdout.write(
                self.style.SUCCESS(f'✅ Очищен кэш рекомендаций для {user.username}')
            )