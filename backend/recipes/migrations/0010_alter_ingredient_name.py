# Generated by Django 3.2.16 on 2023-01-13 17:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0009_alter_recipe_cooking_time'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ingredient',
            name='name',
            field=models.CharField(help_text='Введите название ингредиента', max_length=200, verbose_name='Название ингредиента'),
        ),
    ]