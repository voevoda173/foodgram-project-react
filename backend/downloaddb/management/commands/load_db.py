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
                for ingredient in data:
                    try:
                        Ingredient.objects.create(name=ingredient["name"],
                                                  measurement_unit=ingredient[
                                                      "measurement_unit"])
                    except IntegrityError:
                        print(f'{ingredient["name"]}, '
                              f'{ingredient["measurement_unit"]} '
                              f'был добавлен ранее!')

        except FileNotFoundError:
            raise CommandError('Файл не найден!')
