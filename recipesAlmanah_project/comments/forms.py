from django import forms
from .models import Comment

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text', 'image']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Поделитесь вашим мнением о рецепте...',
                'maxlength': '1000',
                'id': 'commentText'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'id': 'commentImage'
            })
        }
        labels = {
            'text': 'Текст комментария',
            'image': 'Изображение (необязательно)'
        }