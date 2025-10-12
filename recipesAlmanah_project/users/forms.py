from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile

#Класс описывающий форму регистрации пользователя
class UserRegisterForm(UserCreationForm):
   #Прописываем поля для нашей формы, email
    email = forms.EmailField(required=True,
                             widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}))

    #Прописываем поле имени
    first_name = forms.CharField(
    required=False,
    max_length=30,
    widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Имя'}))

    #Прописываем поле фамилии
    last_name = forms.CharField(
        required=False,
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Имя'}))

#Настройка формы
    class Meta:
        #Указывает с какой моделью связана форма
        model = User
        #Определяет перечень полей моделей, которые мы включили в форму
        fields = ['username', 'email','first_name','last_name', 'password1', 'password2']
        #кастоматизация наших html виджетов
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Имя пользователя'}),
        }


        def __init__(self, *args, **kwargs):
            #Инициализация формы со всеми полями
            super(UserRegisterForm, self).__init__(*args, **kwargs)
            #Настройка поля пароля
            self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder':'Пароль'})
            #Настрока поля "Подтверждение пароля"
            self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Подтверждение пароля'})

#Класс отвечающий за изменение данных пользователя на странице пользователя
class UserUpdateForm(forms.ModelForm):
     #Считака нашего поля почты
    email = forms.EmailField()

    #Описание полей на форме
    class Meta:
        #Связь с моделью User
        model = User
        #Перечень полей
        fields = ['username','email','first_name','last_name']

#Класс, отвечающий за поля формы профиля пользователя
class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        #Связь с моделью Профиль
        model = Profile
        #Перечень полей на форме
        fields = ['bio', 'location', 'birth_date', 'profile_photo', 'show_favorites']