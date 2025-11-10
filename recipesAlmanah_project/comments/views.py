from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Comment
from .forms import CommentForm
from recipes.models import Recipe


@login_required
def add_comment(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    if request.method == 'POST':
        form = CommentForm(request.POST, request.FILES)  # Добавляем request.FILES
        if form.is_valid():
            comment = form.save(commit=False)
            comment.recipe = recipe
            comment.author = request.user
            comment.save()
            messages.success(request, 'Ваш комментарий добавлен!')
            return redirect('recipes:recipe-detail', pk=recipe.pk)
    else:
        form = CommentForm()
    return redirect('recipes:recipe-detail', pk=recipe.pk)

@login_required
def delete_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    if request.user == comment.author or request.user.is_superuser:
        recipe_pk = comment.recipe.pk
        comment.delete()
        messages.success(request, 'Комментарий удален!')
        return redirect('recipes:recipe-detail', pk=recipe_pk)
    else:
        messages.error(request, 'Вы не можете удалить этот комментарий!')
        return redirect('recipes:recipe-detail', pk=comment.recipe.pk)