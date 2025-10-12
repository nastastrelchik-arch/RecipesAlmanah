from django import forms
from django.forms import inlineformset_factory
from .models import Recipe, Ingredient, CookingStep

class RecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = ['title', 'description', 'cooking_time', 'servings', 'calories_per_100g', 'difficulty', 'main_photo']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Краткое описание рецепта...'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название рецепта'}),
            'cooking_time': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Время в минутах'}),
            'servings': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Количество порций'}),
            'calories_per_100g': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Калории на 100 грамм'}),
            'difficulty': forms.Select(attrs={'class': 'form-control'}),
            'main_photo': forms.FileInput(attrs={'class': 'form-control'}),
        }

class IngredientForm(forms.ModelForm):
    class Meta:
        model = Ingredient
        fields = ['name', 'quantity']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название ингредиента'}),
            'quantity': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Количество, например: 2 шт, 100 г'}),
        }

class CookingStepForm(forms.ModelForm):
    class Meta:
        model = CookingStep
        fields = ['step_number', 'description', 'photo']
        widgets = {
            'step_number': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Номер шага'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Описание шага...'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }

# Создаем formsets
IngredientFormSet = inlineformset_factory(
    Recipe,
    Ingredient,
    form=IngredientForm,
    extra=3,
    can_delete=True,
    fields=['name', 'quantity']
)

CookingStepFormSet = inlineformset_factory(
    Recipe,
    CookingStep,
    form=CookingStepForm,
    extra=2,
    can_delete=True,
    fields=['step_number', 'description', 'photo']
)