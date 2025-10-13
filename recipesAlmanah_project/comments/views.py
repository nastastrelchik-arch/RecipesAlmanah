# comments/views.py
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Comment
from recipes.models import Recipe

@login_required
def add_comment(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    if request.method == 'POST':
        text = request.POST.get('text')
        Comment.objects.create(recipe=recipe, author=request.user, text=text)
    return redirect('recipes:recipe-detail', pk=recipe_id)