from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from users.models import Follow

User = get_user_model()


class CustomUserAdmin(UserAdmin):
    list_display = ['email', 'username', ]
    list_filter = ['email', 'username', ]


admin.site.register(User, CustomUserAdmin)
admin.site.register(Follow)
