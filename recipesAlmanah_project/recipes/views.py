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
    extra=1,# Одна дополнительная форма
    min_num=0,  # Минимум 0 форм
    validate_min=False,  # Отключить проверку минимального количества
    can_delete=True,
    fields=['name', 'quantity']
)

CookingStepFormSet = inlineformset_factory(
    Recipe,
    CookingStep,
    form=CookingStepForm,
    extra=1, # Одна дополнительная форма
    min_num=0,  # Минимум 0 форм
    validate_min=False,  # Отключить проверку минимального количества
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
        queryset = Recipe.objects.all().prefetch_related('hashtags').order_by('-created_at')

        # Поиск по ключевым словам
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(ingredients__name__icontains=query)
            ).distinct()

        # Фильтрация по нескольким хештегам
        selected_hashtags = self.request.GET.getlist('hashtags')
        if selected_hashtags:
            # Фильтруем рецепты, которые содержат ВСЕ выбранные хештеги
            for hashtag in selected_hashtags:
                queryset = queryset.filter(hashtags__name=hashtag)
            queryset = queryset.distinct()

        # Фильтрация по калорийности
        max_calories = self.request.GET.get('max_calories')
        if max_calories:
            queryset = queryset.filter(calories_per_100g__lte=max_calories)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['all_hashtags'] = Hashtag.objects.all().order_by('name')

        # Получаем список выбранных хештегов для отображения
        selected_hashtags = self.request.GET.getlist('hashtags')
        context['selected_hashtags'] = selected_hashtags

        return context

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
        context = super().get_context_data(**kwargs)
        context['existing_hashtags'] = Hashtag.objects.all().order_by('name')
        if self.request.POST:
            context['ingredient_formset'] = IngredientFormSet(
                self.request.POST, prefix='ingredients'
            )
            context['cooking_step_formset'] = CookingStepFormSet(
                self.request.POST, self.request.FILES, prefix='cooking_steps'
            )
        else:
            context['ingredient_formset'] = IngredientFormSet(
                prefix='ingredients'
            )
            context['cooking_step_formset'] = CookingStepFormSet(
                prefix='cooking_steps'
            )
        return context

    def form_valid(self, form):
        """Сохраняем рецепт и связанные объекты"""
        form.instance.author = self.request.user
        context = self.get_context_data()
        ingredient_formset = context['ingredient_formset']
        cooking_step_formset = context['cooking_step_formset']

        # Сохраняем основной рецепт
        self.object = form.save()

        try:
            # Сохраняем ингредиенты - ВАЖНО: сначала обрабатываем удаленные формы
            if ingredient_formset.is_valid():
                # Получаем все формы, включая отмеченные для удаления
                instances = ingredient_formset.save(commit=False)

                for instance in instances:
                    # Сохраняем только если заполнены оба поля
                    if instance.name and instance.quantity:
                        instance.recipe = self.object
                        instance.save()

                # Удаляем отмеченные для удаления ингредиенты
                for form in ingredient_formset.deleted_forms:
                    if form.instance.pk:
                        form.instance.delete()
            else:
                print("Ingredient formset errors:", ingredient_formset.errors)
                # Если есть ошибки, показываем их пользователю
                return self.render_to_response(self.get_context_data(form=form))

            # Сохраняем шаги приготовления
            if cooking_step_formset.is_valid():
                # Получаем все формы, включая отмеченные для удаления
                instances = cooking_step_formset.save(commit=False)

                for instance in instances:
                    # Сохраняем только если есть описание
                    if instance.description:
                        instance.recipe = self.object
                        instance.save()

                # Удаляем отмеченные для удаления шаги
                for form in cooking_step_formset.deleted_forms:
                    if form.instance.pk:
                        form.instance.delete()
            else:
                print("Cooking step formset errors:", cooking_step_formset.errors)
                # Если есть ошибки, показываем их пользователю
                return self.render_to_response(self.get_context_data(form=form))

            return redirect('recipes:recipe-detail', pk=self.object.pk)

        except Exception as e:
            print(f"Error saving formsets: {e}")
            return self.render_to_response(self.get_context_data(form=form))
#Реадктирование существующего рецепта(только для автора)
class RecipeUpdateView(LoginRequiredMixin, UpdateView):
    model = Recipe
    form_class = RecipeForm
    template_name = 'recipes/recipe_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['existing_hashtags'] = Hashtag.objects.all()

        if self.request.POST:
            context['ingredient_formset'] = IngredientFormSet(
                self.request.POST, self.request.FILES,
                instance=self.object, prefix='ingredients'
            )
            context['cooking_step_formset'] = CookingStepFormSet(
                self.request.POST, self.request.FILES,
                instance=self.object, prefix='cooking_steps'
            )
        else:
            context['ingredient_formset'] = IngredientFormSet(
                instance=self.object, prefix='ingredients'
            )
            context['cooking_step_formset'] = CookingStepFormSet(
                instance=self.object, prefix='cooking_steps'
            )

        return context

    def form_valid(self, form):
        """Сохраняем рецепт и связанные объекты"""
        form.instance.author = self.request.user
        context = self.get_context_data()
        ingredient_formset = context['ingredient_formset']
        cooking_step_formset = context['cooking_step_formset']

        # Сохраняем основной рецепт
        self.object = form.save()

        try:
            # Сохраняем ингредиенты - ВАЖНО: сначала обрабатываем удаленные формы
            if ingredient_formset.is_valid():
                # Получаем все формы, включая отмеченные для удаления
                instances = ingredient_formset.save(commit=False)

                for instance in instances:
                    # Сохраняем только если заполнены оба поля
                    if instance.name and instance.quantity:
                        instance.recipe = self.object
                        instance.save()

                # Удаляем отмеченные для удаления ингредиенты
                for form in ingredient_formset.deleted_forms:
                    if form.instance.pk:
                        form.instance.delete()
            else:
                print("Ingredient formset errors:", ingredient_formset.errors)
                print("Ingredient formset non-form errors:", ingredient_formset.non_form_errors())
                # Если есть ошибки, показываем их пользователю
                return self.render_to_response(self.get_context_data(form=form))

            # Сохраняем шаги приготовления
            if cooking_step_formset.is_valid():
                # Получаем все формы, включая отмеченные для удаления
                instances = cooking_step_formset.save(commit=False)

                for instance in instances:
                    # Сохраняем только если есть описание
                    if instance.description:
                        instance.recipe = self.object
                        instance.save()

                # Удаляем отмеченные для удаления шаги
                for form in cooking_step_formset.deleted_forms:
                    if form.instance.pk:
                        form.instance.delete()
            else:
                print("Cooking step formset errors:", cooking_step_formset.errors)
                print("Cooking step formset non-form errors:", cooking_step_formset.non_form_errors())
                # Если есть ошибки, показываем их пользователю
                return self.render_to_response(self.get_context_data(form=form))

            return redirect('recipes:recipe-detail', pk=self.object.pk)

        except Exception as e:
            print(f"Error saving formsets: {e}")
            return self.render_to_response(self.get_context_data(form=form))

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
    max_calories = request.GET.get('max_calories', '')
    selected_hashtags = request.GET.getlist('hashtags', [])

    recipes = Recipe.objects.all().prefetch_related('hashtags')

    if query:
        recipes = recipes.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(ingredients__name__icontains=query)
        ).distinct()

    # Фильтрация по нескольким хештегам
    if selected_hashtags:
        for hashtag in selected_hashtags:
            recipes = recipes.filter(hashtags__name=hashtag)
        recipes = recipes.distinct()

    if max_calories:
        recipes = recipes.filter(calories_per_100g__lte=max_calories)

    context = {
        'recipes': recipes,
        'query': query,
        'max_calories': max_calories,
        'selected_hashtags': selected_hashtags,
        'all_hashtags': Hashtag.objects.all().order_by('name'),
    }
    return render(request, 'recipes/search_results.html', context)