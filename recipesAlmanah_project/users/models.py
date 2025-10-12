from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

#Описание модели Profile
class Profile(models.Model):
    #Описание полей класса
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=30, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    profile_photo = models.ImageField(upload_to='profile_photos/', null=True, blank=True)
    show_favorites = models.BooleanField(default=True)

    #Описание функции возврата данных
    def __str__(self):
        return f"Профиль: {self.user.username}"

#Сигнал, позволяющий реагировать на изменение данных
@receiver(post_save, sender=User)
#Рассмотрение ситуации создания профиля
def create_user_profile(sender, instance, created, **kwargs):
    #Если пользователь только что создан
    if created:
        #Создание профиля
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    #Добавление для избегание циклического сохранения
    if hasattr(instance, 'profile'):
        instance.profile.save(update_fields=['user'])