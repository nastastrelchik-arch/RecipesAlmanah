from django.contrib import admin
from .models import Recipe, Ingredient, CookingStep, Hashtag, Favorite

class IngredientInline(admin.TabularInline):
    model = Ingredient
    extra = 1

class CookingStepInline(admin.TabularInline):
    model = CookingStep
    extra = 1

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'cooking_time', 'difficulty', 'created_at']
    list_filter = ['difficulty', 'hashtags', 'created_at']
    search_fields = ['title', 'description']
    inlines = [IngredientInline, CookingStepInline]

admin.site.register(Hashtag)
admin.site.register(Favorite)