from django.db.models import F
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (Favorite, Ingredient,
                            IngredientsForRecipe, Tag, Recipe, ShoppingList)
from users.serializers import CustomUserSerializer

User = get_user_model()

MIN_COOKING_TIME = 1
MIN_VALUE_MSG = 'Время приготовления меньше 1'
TYPE_ERROR_MSG = 'Введенное значение не является числом.'
MIN_INGR_MSG = 1
NO_UNIQUE_TAG_MSG = 'Такой тег уже использован.'
MIN_INGR_ERR_MSG = 'Количество ингредиента должно быть больше 0.'
NO_UNIQUE_INGR_MSG = 'Такой ингредиент уже добавлен.'


class IngredientSerializer(serializers.ModelSerializer):
    """Сериалайзер для объектов модели Ingredient."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class TagSerializer(serializers.ModelSerializer):
    """Сериалайзер для объектов модели Tag."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериалайзер для объектов модели Favorite."""

    class Meta:
        model = Favorite
        fields = ('id', 'user', 'recipe')


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Сериалайзер для короткого представления рецепта."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class ShoppingListSerializer(serializers.ModelSerializer):
    """Сериалайзер для объектов модели ShoppingList."""

    class Meta:
        model = ShoppingList
        fields = ('id', 'user', 'recipe')


class IngredientsForRecipeSerializer(serializers.ModelSerializer):
    """Сериалайзер для объектов модели IngredientsForRecipe."""

    id = serializers.ReadOnlyField(source='ingredienrt.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = IngredientsForRecipe
        fields = ['id', 'name', 'measurement_unit', 'amount', ]
        validators = [UniqueTogetherValidator(
            queryset=IngredientsForRecipe.objects.all(),
            fields=['recipe', 'ingredient']
        )
        ]


class RecipeSerializer(serializers.ModelSerializer):
    """Сериалайзер для объектов модели Recipe."""

    ingredients = serializers.SerializerMethodField()
    author = CustomUserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time',
        )

    def create_update_method(self, recipe):
        """Вспомогательная функция для добавления/обновления рецепта."""

        tags = self.initial_data.get('tags')
        for tag in tags:
            recipe.tags.add(get_object_or_404(Tag, pk=tag))
        ingredients = self.initial_data.get('ingredients')
        for ingredient in ingredients:
            IngredientsForRecipe.objects.create(
                ingredient_id=ingredient.get('id'),
                recipe=recipe,
                amount=ingredient.get('amount'),
            )

    def get_ingredients(self, obj):
        return obj.ingredient.values(
            'id', 'name', 'measurement_unit', amount=F('ingr_recipe__amount')
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Favorite.objects.filter(
            user=request.user, recipe=obj
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return ShoppingList.objects.filter(
            user=request.user, recipe=obj
        ).exists()

    def create(self, validated_data):
        author = self.context['request'].user
        recipe = Recipe.objects.create(
            author=author, **validated_data
        )
        self.create_update_method(recipe)
        return recipe

    def update(self, instance, validated_data):
        instance.tags.clear()
        instance.ingredient.clear()
        self.create_update_method(instance)
        return super().update(instance, validated_data)

    def validate(self, data):
        errors = []
        if type(data['cooking_time']) is int:
            if data['cooking_time'] < MIN_COOKING_TIME:
                errors.append(MIN_VALUE_MSG)
        else:
            errors.append(TYPE_ERROR_MSG)

        tags = self.initial_data.get('tags')
        uniq_tag = [0]
        for tag in tags:
            if uniq_tag[-1] == tag:
                errors.append(NO_UNIQUE_TAG_MSG)
                break
            uniq_tag.append(tag)

        ingredients = self.initial_data.get('ingredients')
        uniq_ingr = [0]
        for ingredient in ingredients:
            if int(ingredient['amount']) < MIN_INGR_MSG:
                errors.append(MIN_INGR_ERR_MSG)
            if uniq_ingr[-1] == ingredient['id']:
                errors.append(NO_UNIQUE_INGR_MSG)
            uniq_ingr.append(ingredient['id'])

        if errors:
            raise serializers.ValidationError(errors)
        return data
