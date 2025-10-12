from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


#Описание хештегов
class Hashtag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

#Описание рецептов
class Recipe(models.Model):
    #Поле "сложность" со сразу готовыми вариантами
    DIFFICULTY_LEVELS = [
        ('easy', 'Легкий'),
        ('medium', 'Средний'),
        ('hard', 'Сложный'),
    ]
    #Поля модели
    title = models.CharField(max_length=200)
    description = models.TextField()  # Краткое описание для ленты
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    cooking_time = models.PositiveIntegerField(help_text="Время приготовления в минутах")
    servings = models.PositiveIntegerField(help_text="Количество порций")
    calories_per_100g = models.PositiveIntegerField(help_text="Калории на 100 грамм")
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_LEVELS)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    main_photo = models.ImageField(upload_to='recipes/main_photos/')
    video = models.FileField(upload_to='recipes/videos/', null=True, blank=True)
    hashtags = models.ManyToManyField(Hashtag, blank=True)

    def __str__(self):
        return self.title
#Возврат канонического URL для избегания жёсткого кодирования путей
    def get_absolute_url(self):
        return reverse('recipe-detail', kwargs={'pk': self.pk})

#Описание ингридиента
class Ingredient(models.Model):
    recipe = models.ForeignKey(Recipe, related_name='ingredients', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    quantity = models.CharField(max_length=50)  # Например: "2 шт", "100 г", "по вкусу"

    def __str__(self):
        return f"{self.name} - {self.quantity}"

#Описание шагов готовки
class CookingStep(models.Model):
    recipe = models.ForeignKey(Recipe, related_name='cooking_steps', on_delete=models.CASCADE)
    step_number = models.PositiveIntegerField()
    description = models.TextField()
    photo = models.ImageField(upload_to='recipes/steps_photos/', blank=True, null=True)

    #Сортировка по номеру шага (по возрастранию)
    class Meta:
        ordering = ['step_number']

    def __str__(self):
        return f"Step {self.step_number} for {self.recipe.title}"

#Описание избранного
class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'recipe')

    def __str__(self):
        return f"{self.user.username} - {self.recipe.title}"