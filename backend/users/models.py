from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """Модель пользователя."""

    ROLE_CHOICES = (
        ("user", "user"),
        ("admin", "admin"),
    )

    email = models.EmailField(
        "Адрес электронной почты",
        max_length=254,
        null=False,
        unique=True,
        help_text='Введите адрес электронной почты'
    )
    username = models.CharField(
        "Уникальный юзернейм",
        unique=True,
        max_length=150,
        null=False,
        help_text='Введите свой ник.'
    )
    first_name = models.CharField(
        "Имя",
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
        return self.username[:15]


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
        verbose_name = 'Подписки'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'user'], name='author_follow'
            ),
        ]
