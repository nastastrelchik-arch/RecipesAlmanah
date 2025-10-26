from django import forms
from django.forms import inlineformset_factory
from .models import Recipe, Ingredient, CookingStep, Hashtag

class RecipeForm(forms.ModelForm):
    hashtags_text = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите хештеги через запятую, например: #завтрак, #быстро, #вкусно'
        }),
        help_text="Введите хештеги через запятую. Новые хештеги будут автоматически созданы."
    )

    class Meta:
        model = Recipe
        fields = ['title', 'description', 'cooking_time', 'servings',
                 'calories_per_100g', 'difficulty', 'main_photo']
        widgets = {
            'description': forms.Textarea(
                attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Краткое описание рецепта...'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название рецепта'}),
            'cooking_time': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Время в минутах'}),
            'servings': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Количество порций'}),
            'calories_per_100g': forms.NumberInput(
                attrs={'class': 'form-control', 'placeholder': 'Калории на 100 грамм'}),
            'difficulty': forms.Select(attrs={'class': 'form-control'}),
            'main_photo': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Если редактируем существующий рецепт, заполняем поле хештегов
            hashtags = ', '.join([tag.name for tag in self.instance.hashtags.all()])
            self.fields['hashtags_text'].initial = hashtags

    def clean_hashtags_text(self):
        hashtags_text = self.cleaned_data.get('hashtags_text', '')
        if not hashtags_text:
            return []

        # Разделяем хештеги по запятым и очищаем от пробелов
        hashtag_list = [tag.strip() for tag in hashtags_text.split(',') if tag.strip()]

        # Убеждаемся, что хештеги начинаются с #
        cleaned_hashtags = []
        for tag in hashtag_list:
            if not tag.startswith('#'):
                tag = '#' + tag
            cleaned_hashtags.append(tag)

        return cleaned_hashtags

    def save(self, commit=True):
        # Сначала сохраняем рецепт
        recipe = super().save(commit=commit)

        if commit:
            # Обрабатываем хештеги только после сохранения рецепта
            hashtag_list = self.cleaned_data.get('hashtags_text', [])

            # Очищаем текущие хештеги
            recipe.hashtags.clear()

            # Добавляем новые хештеги
            for tag_name in hashtag_list:
                hashtag, created = Hashtag.objects.get_or_create(name=tag_name)
                recipe.hashtags.add(hashtag)

        return recipe


# Формы для ингредиентов и шагов готовки
class IngredientForm(forms.ModelForm):
    class Meta:
        model = Ingredient
        fields = ['name', 'quantity']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название ингредиента'}),
            'quantity': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Количество, например: 2 шт, 100 г'}),
        }


class CookingStepForm(forms.ModelForm):
    class Meta:
        model = CookingStep
        fields = ['step_number', 'description', 'photo']
        widgets = {
            'step_number': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Номер шага'}),
            'description': forms.Textarea(
                attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Описание шага...'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }


# Formsets
# Создаем formsets
IngredientFormSet = inlineformset_factory(
    Recipe,
    Ingredient,
    form=IngredientForm,
    extra=0,  # Уменьшите extra до 0
    can_delete=True,
    fields=['name', 'quantity'],
    validate_min=False,  # Разрешаем пустые формы
)

CookingStepFormSet = inlineformset_factory(
    Recipe,
    CookingStep,
    form=CookingStepForm,
    extra=0,  # Уменьшите extra до 0
    can_delete=True,
    fields=['step_number', 'description', 'photo'],
    validate_min=False,  # Разрешаем пустые формы
)