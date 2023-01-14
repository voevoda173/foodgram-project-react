from datetime import datetime as dt

from django.contrib.auth.hashers import make_password
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from api.constants import (NO_RECIPE_MSG, NO_SUBSCIBE_MSG,
                           NO_UNIQUE_SUBSCRIBE_MSG, RECIPE_ADDED_MSG,
                           RECIPE_DELETE_MSG, YOUSELF_SUBSCRIBE_DEL_MSG,
                           YOUSELF_SUBSCRIBE_MSG)
from api.filters import IngredientSearchFilter, RecipeFilter
from api.paginators import PageNumberPaginationMod
from api.permissions import IsAdminOrReadOnly, IsAuthorOrStaff
from api.serializers import (CustomUserSerializer, FavoriteSerializer,
                             FollowerSerializer, IngredientSerializer,
                             RecipeSerializer, ShoppingListSerializer,
                             ShortRecipeSerializer, TagSerializer)
from recipes.models import (Favorite, Ingredient, IngredientsForRecipe, Recipe,
                            ShoppingList, Tag)
from users.models import CustomUser, Follow


class SubsctiptionUserViewSet(UserViewSet):
    """Набор представлений для подписки."""

    permission_classes = [IsAdminOrReadOnly]
    serializer_class = CustomUserSerializer
    pagination_class = LimitOffsetPagination

    def perform_create(self, serializer):
        hash_pwd = make_password(serializer.validated_data.get('password'))
        serializer.save(password=hash_pwd)

    @action(methods=['post'], detail=True,
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, id=None):
        """Функция подписки на автора."""

        author = get_object_or_404(CustomUser, pk=id)

        if request.user == author:
            return Response({
                'errors': YOUSELF_SUBSCRIBE_MSG
            }, status=status.HTTP_400_BAD_REQUEST)

        if Follow.objects.filter(user=request.user,
                                 author=author).exists():
            return Response({
                'errors': NO_UNIQUE_SUBSCRIBE_MSG
            }, status=status.HTTP_400_BAD_REQUEST)

        follow = Follow.objects.create(
            user=request.user, author=author
        )
        serializer = FollowerSerializer(
            follow, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, id=None):
        """Функции отписки от автора."""

        author = get_object_or_404(CustomUser, pk=id)

        if request.user == author:
            return Response({
                'errors': YOUSELF_SUBSCRIBE_DEL_MSG
            }, status=status.HTTP_400_BAD_REQUEST)

        subscribe = Follow.objects.filter(user=request.user, author=author)

        if not subscribe.exists():
            return Response({
                'errors': NO_SUBSCIBE_MSG
            }, status=status.HTTP_400_BAD_REQUEST)
        subscribe.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['get'], detail=False,
            permission_classes=[IsAuthenticated], url_path='subscriptions')
    def subscriptions(self, request):
        subscriptions = Follow.objects.filter(user=request.user)
        page = self.paginate_queryset(subscriptions)
        serializer = FollowerSerializer(page, many=True,
                                        context={'request': request})

        return self.get_paginated_response(serializer.data)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Набор представлений для операций с объектами модели Tag."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAdminOrReadOnly, )
    pagination_class = None


class IngredientViewSet(viewsets.ModelViewSet):
    """Набор представлений для операций с объектами модели Ingredient."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (IngredientSearchFilter, )
    search_fields = ('^name', )


class RecipeViewSet(viewsets.ModelViewSet):
    """Набор представлений для операций с объектами модели Recipe."""

    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrStaff, )
    pagination_class = PageNumberPaginationMod
    filter_backends = (DjangoFilterBackend, )
    filterset_class = RecipeFilter

    def create_delete_method(self, models, save_serial, post_serial,
                             request, **kwargs):
        """Вспомогательная функция добавления/удаления рецептов в списки."""

        recipes_list = models.objects.filter(
            user=self.request.user, recipe=kwargs['recipe_id']
        ).exists()

        if request.method == 'POST':
            if recipes_list:
                return Response(
                    RECIPE_ADDED_MSG, status=status.HTTP_400_BAD_REQUEST
                )

            user = self.request.user
            request.data.update({'user': user.id,
                                 'recipe': kwargs['recipe_id']})
            serializer = save_serial(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            recipe = get_object_or_404(Recipe, id=kwargs['recipe_id'])
            serializer = post_serial(recipe)

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if not recipes_list:
                return Response(
                    NO_RECIPE_MSG,
                    status=status.HTTP_400_BAD_REQUEST
                )
            get_object_or_404(
                models, user=self.request.user, recipe=kwargs['recipe_id']
            ).delete()

            return Response(RECIPE_DELETE_MSG,
                            status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['post', 'delete'],
        url_path='(?P<recipe_id>[0-9]+)/shopping_cart',
        detail=False,
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, **kwargs):
        """Функция добавления и удаления рецепта в список покупок."""

        return self.create_delete_method(
            ShoppingList,
            ShoppingListSerializer,
            ShortRecipeSerializer,
            request,
            **kwargs
        )

    @action(
        methods=['post', 'delete'],
        url_path='(?P<recipe_id>[0-9]+)/favorite',
        detail=False,
        permission_classes=[IsAuthenticated],
    )
    def favorite_recipes(self, request, **kwargs):
        """Функция добавления и удаления рецепта в Избранное."""

        return self.create_delete_method(
            Favorite,
            FavoriteSerializer,
            ShortRecipeSerializer,
            request,
            **kwargs
        )

    @action(methods=['get'], detail=False,
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        """Функция формирования PDF-файла со списком покупок."""

        shopping_list = {}
        ingredients = IngredientsForRecipe.objects.filter(
            recipe__shopping_list__user=request.user).values_list(
            'ingredient__name', 'ingredient__measurement_unit',
            'amount')
        for item in ingredients:
            name = item[0]
            if name not in shopping_list:
                shopping_list[name] = {
                    'measurement_unit': item[1],
                    'amount': item[2]
                }
            else:
                shopping_list[name]['amount'] += item[2]
        pdfmetrics.registerFont(
            TTFont('Times', 'times.ttf', 'UTF-8'))
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = ('attachment; '
                                           'filename="Список_покупок.pdf"')
        page = canvas.Canvas(response)
        page.setFont('Times', size=20)
        page.drawString(120, 800,
                        f'Список покупок на {dt.today().strftime("%d.%m.%Y")}')
        page.setFont('Times', size=14)
        height = 750
        for i, (name, data) in enumerate(shopping_list.items(), 1):
            page.drawString(75, height, (f'{i}. {name} - {data["amount"]}, '
                                         f'{data["measurement_unit"]}'))
            height -= 25
        page.showPage()
        page.save()
        return response
