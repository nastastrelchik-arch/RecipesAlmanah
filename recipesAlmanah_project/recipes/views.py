from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.db.models import Q
from .models import Recipe, Favorite, Hashtag, Ingredient, CookingStep
from .forms import RecipeForm, IngredientForm, CookingStepForm

# Импортируем inlineformset_factory и создаем formsets прямо в views
from django.forms import inlineformset_factory, formset_factory

# Создаем formsets здесь, чтобы избежать циклических импортов
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

#Отображение списка рецептов с поддержкой пагинации(разделение на мелкие части), поиска и фильтрации
class RecipeListView(ListView):
    #Связь с Recipe
    model = Recipe
    #Ссылка на шаблон
    template_name = 'recipes/home.html'
    #Имя переменной в контексте шаблона
    context_object_name = 'recipes'
    #Количество рецептов на странице
    paginate_by = 9

    def get_queryset(self):
        queryset = Recipe.objects.all().order_by('-created_at')

        # Поиск по ключевым словам в названии, описании, ингридиентах
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(ingredients__name__icontains=query)
            ).distinct()

        # Фильтрация по хештегам
        hashtag = self.request.GET.get('hashtag')
        if hashtag:
            queryset = queryset.filter(hashtags__name=hashtag)

        # Фильтрация по калорийности
        max_calories = self.request.GET.get('max_calories')
        if max_calories:
            queryset = queryset.filter(calories_per_100g__lte=max_calories)

        return queryset

#Отображение детальной информации о конкретном рецепте
class RecipeDetailView(DetailView):
    model = Recipe
    template_name = 'recipes/recipe_detail.html'

#Создание нового рецепта(только для авторизованных пользователей)
class RecipeCreateView(LoginRequiredMixin, CreateView):
    model = Recipe
    form_class = RecipeForm
    template_name = 'recipes/recipe_form.html'

    def get_context_data(self, **kwargs):
        """Добавляем formsets в контекст"""
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['ingredient_formset'] = IngredientFormSet(self.request.POST, self.request.FILES,
                                                              prefix='ingredients')
            context['cooking_step_formset'] = CookingStepFormSet(self.request.POST, self.request.FILES,
                                                                 prefix='cooking_steps')
        else:
            context['ingredient_formset'] = IngredientFormSet(prefix='ingredients')
            context['cooking_step_formset'] = CookingStepFormSet(prefix='cooking_steps')
        return context

    def form_valid(self, form):
        """Сохраняем рецепт и связанные объекты"""
        form.instance.author = self.request.user
        context = self.get_context_data()
        ingredient_formset = context['ingredient_formset']
        cooking_step_formset = context['cooking_step_formset']

        # Сохраняем основной рецепт
        self.object = form.save()

        # Сохраняем ингредиенты
        if ingredient_formset.is_valid():
            ingredient_formset.instance = self.object
            ingredient_formset.save()
        else:
            print("Ingredient formset errors:", ingredient_formset.errors)

        # Сохраняем шаги приготовления
        if cooking_step_formset.is_valid():
            cooking_step_formset.instance = self.object
            cooking_step_formset.save()
        else:
            print("Cooking step formset errors:", cooking_step_formset.errors)

        return redirect('recipes:recipe-detail', pk=self.object.pk)

    def form_invalid(self, form):
        """Обработка невалидной формы"""
        return self.render_to_response(self.get_context_data(form=form))


#Реадктирование существующего рецепта(только для автора)
class RecipeUpdateView(LoginRequiredMixin, UpdateView):
    model = Recipe
    form_class = RecipeForm
    template_name = 'recipes/recipe_form_update.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['ingredient_formset'] = IngredientFormSet(self.request.POST, self.request.FILES,
                                                              instance=self.object, prefix='ingredients')
            context['cooking_step_formset'] = CookingStepFormSet(self.request.POST, self.request.FILES,
                                                                 instance=self.object, prefix='cooking_steps')
        else:
            context['ingredient_formset'] = IngredientFormSet(instance=self.object, prefix='ingredients')
            context['cooking_step_formset'] = CookingStepFormSet(instance=self.object, prefix='cooking_steps')
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        ingredient_formset = context['ingredient_formset']
        cooking_step_formset = context['cooking_step_formset']

        if ingredient_formset.is_valid() and cooking_step_formset.is_valid():
            self.object = form.save()
            ingredient_formset.instance = self.object
            ingredient_formset.save()
            cooking_step_formset.instance = self.object
            cooking_step_formset.save()
            return redirect('recipes:recipe-detail', pk=self.object.pk)
        else:
            return self.render_to_response(self.get_context_data(form=form))

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.author != self.request.user:
            return redirect('recipes:recipe-detail', pk=obj.pk)
        return super().dispatch(request, *args, **kwargs)

#Удаление рецепта(только для автора)
class RecipeDeleteView(LoginRequiredMixin, DeleteView):
    model = Recipe
    template_name = 'recipes/recipe_confirm_delete.html'
    success_url = '/'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        #Вновь проверка на авторство
        if obj.author != self.request.user:
            return redirect('recipes:recipe-detail', pk=obj.pk)
        return super().dispatch(request, *args, **kwargs)

#Добавление(если нет)/удаление(если был) в избранное
@login_required
def add_to_favorites(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    favorite, created = Favorite.objects.get_or_create(user=request.user, recipe=recipe)
    if not created:
        favorite.delete()
    return redirect('recipes:recipe-detail', pk=pk)

#Реализует расширенный поиск рецептов с фильтрацией
def search_recipes(request):
    query = request.GET.get('q', '')
    hashtag = request.GET.get('hashtag', '')
    max_calories = request.GET.get('max_calories', '')

    recipes = Recipe.objects.all()

    if query:
        recipes = recipes.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(ingredients__name__icontains=query)
        ).distinct()

    if hashtag:
        recipes = recipes.filter(hashtags__name=hashtag)

    if max_calories:
        recipes = recipes.filter(calories_per_100g__lte=int(max_calories))

    context = {
        'recipes': recipes,
        'query': query,
        'hashtag': hashtag,
        'max_calories': max_calories,
    }

    return render(request, 'recipes/search_results.html', context)