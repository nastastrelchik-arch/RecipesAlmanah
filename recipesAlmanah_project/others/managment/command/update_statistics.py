from django.core.management.base import BaseCommand
from others.models import Statistic

class Command(BaseCommand):
    help = 'Обновить статистику сайта'

    def handle(self, *args, **options):
        try:
            Statistic.update_site_statistics()
            self.stdout.write(
                self.style.SUCCESS('Статистика успешно обновлена!')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка при обновлении статистики: {str(e)}')
            )