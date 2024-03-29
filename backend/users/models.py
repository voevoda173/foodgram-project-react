from django.contrib.auth.models import AbstractUser
from django.db import models

from api.constants import STR_LENGHT


class CustomUser(AbstractUser):
    """Модель пользователя."""

    ADMIN = 'admin'
    USER = 'user'
    ROLE_CHOICES = (
        (ADMIN, 'Administrator'),
        (USER, 'User'),
    )

    email = models.EmailField(
        verbose_name="Адрес электронной почты",
        max_length=254,
        null=False,
        unique=True,
        help_text='Введите адрес электронной почты',
    )
    username = models.CharField(
        verbose_name="Уникальный юзернейм",
        unique=True,
        max_length=150,
        null=False,
        help_text='Введите свой ник.'
    )
    first_name = models.CharField(
        verbose_name="Имя",
        max_length=150,
        null=False,
        help_text='Введите свое имя'
    )
    last_name = models.CharField(
        "Фамилия",
        max_length=150,
        null=False,
        help_text='Введите свою фамилию'
    )
    password = models.CharField(
        "Пароль",
        max_length=150,
    )
    role = models.CharField(
        max_length=100,
        choices=ROLE_CHOICES,
        default="user",
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.username[:STR_LENGHT]

    @property
    def is_admin(self):
        return (self.is_superuser or self.role == self.ADMIN
                or self.is_staff)


class Follow(models.Model):
    """Класс для создания подписок."""

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='follower',
    )
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='following',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'user'], name='author_follow'
            ),
        ]
