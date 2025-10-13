from django.urls import path
from . import views

app_name = 'comments'

urlpatterns = [
    path('recipe/<int:recipe_id>/comment/', views.add_comment, name='add-comment'),
]