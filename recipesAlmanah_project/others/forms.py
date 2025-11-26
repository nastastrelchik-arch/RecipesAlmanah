# others/forms.py
from django import forms
from .models import Article, Recommendation, ArticleProposal
from django.core.exceptions import ValidationError

class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['title', 'article_type', 'content', 'main_image', 'hashtags', 'status']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите заголовок статьи'
            }),
            'article_type': forms.Select(attrs={
                'class': 'form-control article-type-select'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control article-content',
                'rows': 15,
                'placeholder': 'Содержание статьи'
            }),
            'main_image': forms.ClearableFileInput(attrs={
                'class': 'form-control article-main-image',
                'accept': 'image/*'
            }),
            'hashtags': forms.SelectMultiple(attrs={
                'class': 'form-control'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'title': 'Заголовок',
            'article_type': 'Тип статьи',
            'content': 'Содержание',
            'main_image': 'Главное изображение',
            'hashtags': 'Хештеги',
            'status': 'Статус',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Делаем поля условно обязательными в зависимости от типа статьи
        self.fields['content'].required = False
        self.fields['main_image'].required = False

    def clean(self):
        cleaned_data = super().clean()
        article_type = cleaned_data.get('article_type')
        content = cleaned_data.get('content', '').strip()
        main_image = cleaned_data.get('main_image')

        if article_type == 'text_only' and not content:
            self.add_error('content', 'Для текстовой статьи необходимо заполнить содержание')

        if article_type == 'photo_only' and not main_image and not self.instance.main_image:
            self.add_error('main_image', 'Для фото-статьи необходимо загрузить главное изображение')

        if article_type == 'mixed' and not content and not main_image and not self.instance.main_image:
            self.add_error(
                'content',
                'Для смешанной статьи необходимо заполнить содержание ИЛИ загрузить изображение'
            )
            self.add_error(
                'main_image',
                'Для смешанной статьи необходимо заполнить содержание ИЛИ загрузить изображение'
            )

        return cleaned_data

class ArticleProposalForm(forms.ModelForm):
    class Meta:
        model = ArticleProposal
        fields = ['title', 'content', 'author_name', 'author_email', 'contact_phone']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите заголовок предлагаемой статьи'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 12,
                'placeholder': 'Опишите идею статьи, основные тезисы или приложите готовый текст...'
            }),
            'author_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ваше имя'
            }),
            'author_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ваш email для связи'
            }),
            'contact_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ваш телефон (необязательно)'
            }),
        }
        labels = {
            'title': 'Заголовок предложения',
            'content': 'Содержание предложения',
            'author_name': 'Ваше имя',
            'author_email': 'Email для связи',
            'contact_phone': 'Телефон',
        }

    def clean_content(self):
        content = self.cleaned_data.get('content')
        if len(content.strip()) < 50:
            raise ValidationError('Описание предложения должно содержать не менее 50 символов.')
        return content

class ArticleProposalReviewForm(forms.ModelForm):
    class Meta:
        model = ArticleProposal
        fields = ['status', 'admin_notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'admin_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Комментарии для автора предложения...'
            }),
        }
        labels = {
            'status': 'Решение по предложению',
            'admin_notes': 'Комментарии администратора',
        }

class RecommendationForm(forms.ModelForm):
    class Meta:
        model = Recommendation
        fields = ['title', 'description', 'recommendation_type', 'recipes', 'is_active', 'order']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'recommendation_type': forms.Select(attrs={'class': 'form-control'}),
            'recipes': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'title': 'Заголовок',
            'description': 'Описание',
            'recommendation_type': 'Тип рекомендации',
            'recipes': 'Рекомендуемые рецепты',
            'is_active': 'Активно',
            'order': 'Порядок отображения',
        }