from django.contrib import admin
from .models import Axe, Portefeuille, Programme, Projet, Composante, Activite, Probleme, Message, CustomUser

from django.contrib.auth.admin import UserAdmin
# Register your models here.


admin.site.register(Axe)
admin.site.register(Portefeuille)
admin.site.register(Programme)
admin.site.register(Projet)
admin.site.register(Composante)
admin.site.register(Activite)
admin.site.register(Probleme)
admin.site.register(Message)




class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'nom', 'role', 'is_staff', 'is_active') 
    fieldsets = UserAdmin.fieldsets + (
        ('Informations complémentaires', {'fields': ('nom', 'role')}),  
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informations complémentaires', {'fields': ('nom', 'role')}),
    )


admin.site.register(CustomUser, CustomUserAdmin)


