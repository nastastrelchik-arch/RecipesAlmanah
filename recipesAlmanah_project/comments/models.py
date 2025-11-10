from django.db import models
from django.contrib.auth.models import User
from recipes.models import Recipe


#Модель для предстваления публикаций на сайте
class CommentArticle(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    published_at = models.DateTimeField(auto_now_add=True)
    hashtags = models.ManyToManyField('recipes.Hashtag', blank=True)

    def __str__(self):
        return self.title

#Модель для представления комментариев к рецептам
# Модель для представления комментариев к рецептам
class Comment(models.Model):
    # При удалении рецепта удалятся и все комменты
    recipe = models.ForeignKey(Recipe, related_name='comments', on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to='comments/images/', blank=True, null=True)

    # Сортировка по дате публикации
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Comment by {self.author.username} on {self.recipe.title}"