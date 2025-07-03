from django.contrib import admin
from .models import Axe, Portefeuille, Programme, Projet, Composante, Activite, Probleme, Message, CustomUser

from django.contrib.auth.admin import UserAdmin
# Register your models here.


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'nom', 'role', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'nom')
    ordering = ('-date_joined',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('Informations supplémentaires', {'fields': ('role', 'nom')}),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informations supplémentaires', {
            'fields': ('role', 'nom', 'email'),
        }),
    )

admin.site.register(Axe)
admin.site.register(Portefeuille)
admin.site.register(Programme)
admin.site.register(Projet)
admin.site.register(Composante)
admin.site.register(Activite)
admin.site.register(Probleme)
admin.site.register(Message)
admin.site.register(CustomUser, CustomUserAdmin)


