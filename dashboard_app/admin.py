from django.contrib import admin
from .models import User, Axe, Portefeuille, Programme, Projet, Composante, Activite, Probleme, Message
# Register your models here.

admin.site.register(User)
admin.site.register(Axe)
admin.site.register(Portefeuille)
admin.site.register(Programme)
admin.site.register(Projet)
admin.site.register(Composante)
admin.site.register(Activite)
admin.site.register(Probleme)
admin.site.register(Message)


from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'nom', 'role', 'is_staff', 'is_active')  # Ajout nom dans liste
    fieldsets = UserAdmin.fieldsets + (
        ('Informations complémentaires', {'fields': ('nom', 'role')}),  # Ajouter nom et role dans le formulaire
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informations complémentaires', {'fields': ('nom', 'role')}),
    )


admin.site.register(CustomUser, CustomUserAdmin)


