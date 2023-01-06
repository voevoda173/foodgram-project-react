from django.contrib import admin

from .models import (Favorite, Ingredient, IngredientsForRecipe,
                     Recipe, ShoppingList, Tag)


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit',)
    search_fields = ('name',)
    list_filter = ('name',)


class IngredientForRecipeAdmin(admin.TabularInline):
    model = IngredientsForRecipe
    fk_name = 'recipe'


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('author', 'name', 'favorites', )
    list_filter = ('author', 'name', 'tags')
    search_fields = ('author',)
    exclude = ('ingredients',)
    inlines = [IngredientForRecipeAdmin, ]

    def favorites(self, obj):
        """Получение количества добавлений рецепта в избранное."""

        return Favorite.objects.filter(recipe=obj).count()

    favorites.short_description = "Количество добавлений в избранное."


class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug')


class ShoppingListAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')


class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')


class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount')


admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(ShoppingList, ShoppingListAdmin)
admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(IngredientsForRecipe, RecipeIngredientAdmin)
