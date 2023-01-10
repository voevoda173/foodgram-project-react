import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.utils import IntegrityError

from recipes.models import Ingredient

DATA_ROOT = os.path.join(settings.BASE_DIR, 'data')


class Command(BaseCommand):
    help = 'Загрузка ингредиентов из файла CSS в базу данных.'

    def add_arguments(self, parser):
        parser.add_argument('filename', default='ingredients.json', nargs='?',
                            type=str)

    def handle(self, *args, **options):
        try:
            with open(os.path.join(DATA_ROOT, options['filename']), 'r',
                      encoding='utf-8') as f:
                data = json.load(f)
                ingredients = [
                    Ingredient(
                        name=ingredient.get('name'),
                        measurement_unit=ingredient.get('measurement_unit')
                    )
                    for ingredient in data
                ]

                try:
                    Ingredient.objects.bulk_create(ingredients)
                except IntegrityError:
                    print('Неуникальные элементы не добавлены.')

        except FileNotFoundError:
            raise CommandError('Файл не найден!')
