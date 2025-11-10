from django.urls import path
from . import views

app_name = 'comments'

urlpatterns = [
    path('recipe/<int:pk>/comment/', views.add_comment, name='add-comment'),
    path('comment/<int:pk>/delete/', views.delete_comment, name='delete-comment'),
]