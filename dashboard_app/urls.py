from django.contrib import admin
from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    # path('admin/', admin.site.urls),
    path('home/', views.home_view),
    path('menu/', views.menu_view, name='menu'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard_coordo/', views.dashboard_coordo_view, name='dashboard_coordo'),
    path('tables/', views.table_view, name='tables'),
    path('notifications/', views.notification_view, name='notifications'),
    path('data_get_view/', views.data_get_view, name='data_get_view'),
    path('tables/projets/', views.projets_data_view, name='tables_sub1'),
    path('tables/composantes/', views.composantes_data_view, name='tables_sub2'),
    path('tables/activites/', views.activites_data_view, name='tables_sub3'),
    path('tables/problemes/', views.problemes_data_view, name='tables_sub4'),
    path('ajout_projet/', views.ajouter_projet, name='ajout_projet'),
    path('modifie_projet/<str:pk>', views.modifie_projet, name='modifie_projet'),
    path('ajout_activite/', views.ajouter_activite, name='ajout_activite'),
    path('modifie_activite/<str:rk>', views.modifie_activite, name='modifie_activite'),
    path('ajout_probleme/', views.ajouter_probleme, name='ajout_probleme'),
    path('modifie_probleme/<str:rk>', views.modifie_probleme, name='modifie_probleme'),
    path('ajout_composante/', views.ajouter_composante, name='ajout_composante'),
    path('modifie_composante/<str:rk>', views.modifie_composante, name='modifie_composante'),
    path('', views.sing_in, name='sing_in'),
    path('register', views.sing_up, name='sing_up'),
    path('logout', views.log_out, name='log_out'),
    path('forgot-password', views.forgot_password, name='forgot_password'),
    path('update-password', views.update_password, name='update_password'),
    path('profile', views.profile_view, name='profile'),
    # Changement de mot de passe
    path('change-password/', auth_views.PasswordChangeView.as_view(
        template_name='registration/change_password.html',
        success_url='/profile/'
    ), name='change_password'),
    # URLs d'authentification par défaut (optionnel mais recommandé)
    path('accounts/', include('django.contrib.auth.urls')),
    path('tables/problemes/import-csv/', views.import_csv_problem, name='import_problem'),
    path('tables/activites/import-csv/', views.import_csv_activite, name='import_activite'),
    path('tables/projets/import-csv/', views.import_csv_projets, name='import_projet'),

    


    path('dashboard_coordo2/', views.dashboard_coordo, name='dashboard_coordo2'),
    path('get-filter-options/', views.get_filter_options, name='get_filter_options'),
    path('get-stats/', views.get_stats, name='get_stats'),



    path('api/filters/l2/', views.l2_filter_options, name='l2_filter_options'),
    path('api/filters/l3/', views.l3_filter_options, name='l3_filter_options'),
    path('api/filters/l4/', views.l4_filter_options, name='l4_filter_options'),
    path('api/filters/l5/', views.l5_filter_options, name='l5_filter_options'),
    path('api/stats/', views.get_stats, name='get_stats'),
    path('api/stats/global/', views.global_stats, name='global_stats'),
    path('api/composantes/<int:composante_id>/', views.composante_details, name='composante_details'),
    path('api/messages/', views.get_messages, name='get_messages'),
]

