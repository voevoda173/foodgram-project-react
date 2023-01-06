from django_filters import (AllValuesMultipleFilter)
from django_filters.rest_framework import FilterSet, filters
from rest_framework.filters import SearchFilter

from recipes.models import Recipe


class IngredientSearchFilter(SearchFilter):
    """Поиск ингредиентов."""

    search_param = 'name'


class RecipeFilter(FilterSet):
    """Фильтр для объектов модели Recipe."""

    author = AllValuesMultipleFilter(field_name='author__id')
    tags = AllValuesMultipleFilter(field_name='tags__slug')
    is_favorited = filters.BooleanFilter(method='get_is_favorited')
    is_in_shopping_list = filters.BooleanFilter(
        method='get_is_in_shopping_list')

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_list')

    def get_is_favorited(self, queryset, name, value):
        """Показывает только избранные рецепты."""

        if self.request.user.is_authenticated and value:
            return queryset.filter(favorite__user=self.request.user)

        return queryset

    def get_is_in_shopping_list(self, queryset, name, value):
        """Показывает рецепты, добавленные в список покупок."""

        if self.request.user.is_authenticated and value:
            return queryset.filter(shopping_list__user=self.request.user)

        return queryset
