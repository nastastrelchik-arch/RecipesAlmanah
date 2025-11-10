from django import forms
from .models import Article, Recommendation

class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['title', 'content', 'main_image', 'hashtags', 'is_published']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите заголовок статьи'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 10, 'placeholder': 'Содержание статьи'}),
            'main_image': forms.FileInput(attrs={'class': 'form-control'}),
            'hashtags': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'title': 'Заголовок',
            'content': 'Содержание',
            'main_image': 'Главное изображение',
            'hashtags': 'Хештеги',
            'is_published': 'Опубликовать',
        }

class RecommendationForm(forms.ModelForm):
    class Meta:
        model = Recommendation
        fields = ['title', 'content', 'recommendation_type', 'related_recipe', 'related_article', 'is_active', 'order']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'recommendation_type': forms.Select(attrs={'class': 'form-control'}),
            'related_recipe': forms.Select(attrs={'class': 'form-control'}),
            'related_article': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }