from django.db.models import F
from django.shortcuts import get_object_or_404
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from api.constants import (ERROR_NAME_MSG, MIN_COOKING_TIME, MIN_INGR_ERR_MSG,
                           MIN_INGR_MSG, MIN_VALUE_MSG, NO_UNIQUE_EMAIL_MSG,
                           NO_UNIQUE_INGR_MSG, NO_UNIQUE_NAME_MSG,
                           NO_UNIQUE_TAG_MSG, TYPE_ERROR_MSG)
from recipes.models import (Favorite, Ingredient, IngredientsForRecipe, Recipe,
                            ShoppingList, Tag)
from users.models import CustomUser, Follow


class CustomUserSerializer(serializers.ModelSerializer):
    """Сериалайзер пользователя."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed')

    def get_is_subscribed(self, obj):

        request = self.context.get('request')

        if request.user.is_anonymous or request is None:
            return False

        return Follow.objects.filter(user=request.user, author=obj.id).exists()


class RegSerializer(serializers.ModelSerializer):
    """Сериалайзер, применяемый при регистрации пользователя."""

    email = serializers.EmailField(required=True, max_length=254)
    username = serializers.CharField(required=True, max_length=150)
    first_name = serializers.CharField(required=True, max_length=150)
    last_name = serializers.CharField(required=True, max_length=150)

    def validate_email(self, value):

        lower_email = value.lower()

        if CustomUser.objects.filter(email=lower_email).exists():
            raise serializers.ValidationError(NO_UNIQUE_EMAIL_MSG)

        return lower_email

    def validate_username(self, value):

        if value.lower() == 'me':
            raise serializers.ValidationError(ERROR_NAME_MSG)

        if CustomUser.objects.filter(username=value).exists():
            raise serializers.ValidationError(NO_UNIQUE_NAME_MSG)

        return value

    class Meta:
        model = CustomUser
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'password')


class FollowRecipeSerializer(serializers.ModelSerializer):
    """Сериалайзер для рецептов подписчика."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time', )


class FollowerSerializer(serializers.ModelSerializer):
    """Сериалайзер подписки."""

    email = serializers.ReadOnlyField(source='author.email')
    id = serializers.ReadOnlyField(source='author.id')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Follow
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count')

    def get_is_subscribed(self, obj):

        request = self.context.get('request')
        if request.user.is_anonymous or request is None:
            return False

        return Follow.objects.filter(user=request.user,
                                     author=obj.author).exists()

    def get_recipes(self, obj):

        recipes = Recipe.objects.filter(author=obj.author)

        return FollowRecipeSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.author).count()


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

    id = serializers.ReadOnlyField(source='ingredient.id')
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
        return Favorite.objects.filter(
            user=request.user, recipe=obj
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
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
