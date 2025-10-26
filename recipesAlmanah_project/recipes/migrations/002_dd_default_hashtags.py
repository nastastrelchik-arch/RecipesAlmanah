# recipes/migrations/0002_add_default_hashtags.py
from django.db import migrations


def add_default_hashtags(apps, schema_editor):
    Hashtag = apps.get_model('recipes', 'Hashtag')
    default_hashtags = [
        '#завтрак', '#обед', '#ужин', '#десерт', '#выпечка',
        '#здоровое', '#быстро', '#праздник', '#вегетарианское', '#мясо',
        '#рыба', '#салат', '#суп', '#напиток', '#закуска'
    ]

    for tag_name in default_hashtags:
        Hashtag.objects.get_or_create(name=tag_name)


def remove_default_hashtags(apps, schema_editor):
    Hashtag = apps.get_model('recipes', 'Hashtag')
    default_hashtags = [
        '#завтрак', '#обед', '#ужин', '#десерт', '#выпечка',
        '#здоровое', '#быстро', '#праздник', '#вегетарианское', '#мясо',
        '#рыба', '#салат', '#суп', '#напиток', '#закуска'
    ]

    Hashtag.objects.filter(name__in=default_hashtags).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('recipes', '0001_initial'),  # замените на актуальную миграцию
    ]

    operations = [
        migrations.RunPython(add_default_hashtags, remove_default_hashtags),
    ]