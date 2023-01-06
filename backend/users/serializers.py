from rest_framework import serializers

from recipes.models import Recipe
from users.models import CustomUser, Follow


NO_UNIQUE_EMAIL_MSG = 'Такая электронная почта уже используется.'
ERROR_NAME_MSG = 'Нельзя использовать такое имя.'
NO_UNIQUE_NAME_MSG = 'Пользователь с таким именеи уже существует.'


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


class FollowRecipeSerializer(serializers.ModelSerializer):
    """Сериалайзер для рецептов подписчика."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time', )


class FollowerSerializer(serializers.Serializer):
    """Сериалайзер подписчика."""

    email = serializers.ReadOnlyField()
    id = serializers.ReadOnlyField()
    username = serializers.ReadOnlyField()
    first_name = serializers.ReadOnlyField()
    last_name = serializers.ReadOnlyField()
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

        return Follow.objects.filter(user=request.user, author=obj.id).exists()

    def get_recipes(self, obj):

        recipes = Recipe.objects.filter(author=obj)

        return FollowRecipeSerializer(recipes, many=True).data

    def get_recipes_count(self, author):
        return Recipe.objects.filter(author=author).count()
