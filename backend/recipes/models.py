from colorfield.fields import ColorField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from api.constants import (MAX_COOK_TIME_VALUE, MAX_COOK_TIME_VALUE_MSG,
                           MIN_COOK_TIME_VALUE, MIN_COOK_TIME_VALUE_MSG,
                           STR_LENGHT)
from users.models import CustomUser


class Tag(models.Model):
    """Класс для создания объектов модели Тэг."""

    name = models.CharField(
        verbose_name='Название тэга',
        max_length=200,
        unique=True,
        null=False,
        help_text='Введите имя тэга'
    )
    color = ColorField(
        verbose_name='Цвет тэга',
        max_length=7,
        unique=True,
        default='#42aaff',
        help_text='Введите HEX-код цвета тэга',
    )
    slug = models.SlugField(
        verbose_name='Уникальный слаг тэга',
        max_length=200,
        unique=True,
        null=False,
        help_text='Введите slug тэга',

    )

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'
        ordering = ('name', )

    def __str__(self):
        return self.name[:STR_LENGHT]


class Ingredient(models.Model):
    """Класс для создания объктов модели Ингредиент."""

    name = models.CharField(
        verbose_name='Название ингредиента',
        max_length=200,
        unique=True,
        null=False,
        help_text='Введите название ингредиента',
    )
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=200,
        null=False,
        help_text='Введите название единицы измерения'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name', )

    def __str__(self):
        return self.name[:STR_LENGHT]


class Recipe(models.Model):
    """Класс для создания объектов модели рецепт."""

    ingredient = models.ManyToManyField(
        Ingredient,
        related_name='recipes',
        verbose_name='Ингредиенты',
        through='IngredientsForRecipe',
        help_text='Выберите ингредиенты'
    )

    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
        help_text='Веберите тэги.',
        related_name='recipes'
    )

    image = models.ImageField(
        verbose_name='Фото блюда',
        upload_to='',
        null=False,
        blank=True,
        help_text='Прикрепите фото готового блюда'
    )

    name = models.CharField(
        verbose_name='Название блюда',
        max_length=200,
        null=False,
        help_text='Введите название блюда',
    )

    text = models.TextField(
        verbose_name='Описание рецепта',
        null=False,
        help_text='Напишите свой рецепт',
    )

    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления (минут)',
        validators=[
            MinValueValidator(
                MIN_COOK_TIME_VALUE, message=MIN_COOK_TIME_VALUE_MSG),
            MaxValueValidator(
                MAX_COOK_TIME_VALUE, message=MAX_COOK_TIME_VALUE_MSG),
        ],
        null=False,
        help_text='Введите время приготовления блюда в минутах',
    )

    author = models.ForeignKey(
        CustomUser,
        verbose_name='Автор рецепта',
        on_delete=models.CASCADE,
        null=False,
        related_name='recipes',
    )

    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('id', )

    def __str__(self):
        return self.name[:15]

    def get_tags(self):
        return '\n'.join([t.tags for t in self.tags.all()])

    def get_ingredients(self):
        return '\n'.join([i.ingredients for i in self.ingredients.all()])


class IngredientsForRecipe(models.Model):
    """Количество ингредиентов в рецепте."""

    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingr_recipe',
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingr_recipe',
    )

    amount = models.PositiveIntegerField(
        verbose_name='Количество'
    )

    class Meta:
        verbose_name = 'Количество ингредиента'
        verbose_name_plural = 'Количество ингредиентов'
        constraints = [
            models.UniqueConstraint(fields=[
                'ingredient',
                'recipe',
            ],
                name='ingredient_recipe_unique'),
        ]

    def __str__(self):
        return (f'{self.ingredient.name} - {self.amount} '
                f'({self.ingredient.measurement_unit})')


class Favorite(models.Model):
    """Класс для создания объектов Избранные рецепты."""

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='favorite',
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='favorite',
    )

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='recipe_favorite'
            ),
        ]
        ordering = ('recipe__pub_date', )


class ShoppingList(models.Model):
    """Класс для создания объектов модели Список покупок."""

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='shopping_list',
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='recipe_shopping_list'
            ),
        ]
        ordering = ('recipe__pub_date', )
