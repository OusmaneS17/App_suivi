# Django core
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.core.mail import EmailMessage
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from django.core.validators import validate_email
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required

# Forms
from .forms import ProjetForm, ActiviteForm, ProblemeForm, ComposanteForm, UploadCSVForm, MessageForm

# Models
from .models import *

# CSV + fichiers
from io import TextIOWrapper
import csv
import json
from decimal import Decimal
from datetime import date, datetime
from pathlib import Path
from django.forms import Form, FileField

# Django simple history
from simple_history.utils import update_change_reason
# from simple_history.utils import get_history_model  # à décommenter si nécessaire

# Requêtes complexes
from django.db.models import Q, Count

# Visualisation
import plotly.express as px
from plotly import graph_objs as go
from plotly.offline import plot

# Cartographie
import folium



# Create your views here.

from dashboard_app.models import CustomUser  # Import de ton modèle utilisateur personnalisé


def sing_in(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = CustomUser.objects.filter(email=email).first()
        if user:
            # Ici on utilise username car authenticate attend username (ou modifié dans AUTHENTICATION_BACKENDS)
            auth_user = authenticate(request, username=user.username, password=password)
            if auth_user:
                login(request, auth_user)
                return redirect('dashboard')
            else:
                messages.error(request, "Mot de passe incorrect")
        else:
            messages.error(request, "Aucun utilisateur avec cet email")

    return render(request, 'authentification/login.html')


def sing_up(request):
    error = False
    message = ""
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        repassword = request.POST.get('repassword')

        # Validation email
        try:
            validate_email(email)
        except:
            error = True
            message = "Veuillez entrer un email valide svp !"

        # Vérifier mots de passe
        if not error and password != repassword:
            error = True
            message = "Les deux mots de passe ne correspondent pas !"

        # Vérifier existence d'un utilisateur avec email ou username
        if not error:
            user = CustomUser.objects.filter(Q(email=email) | Q(username=name)).first()
            if user:
                error = True
                message = f"Un utilisateur avec email {email} ou nom d'utilisateur {name} existe déjà !"

        # Création utilisateur
        if not error:
            user = CustomUser(
                username=name,
                email=email,
                nom=name  # si tu as un champ 'nom' dans CustomUser
            )
            user.set_password(password)  # hash automatique
            user.save()

            messages.success(request, "Inscription réussie ! Vous pouvez maintenant vous connecter.")
            return redirect('sing_in')

    context = {
        'error': error,
        'message': message
    }
    return render(request, 'authentification/register.html', context)


def log_out(request):
    logout(request)
    return redirect('sing_in')


def forgot_password(request):
    error = False
    success = False
    message = ""
    if request.method == 'POST':
        email = request.POST.get('email')
        user = User.objects.filter(email=email).first()
        if user:
            print("processing forgot password")
            html = """
                <p> Hello, merci de cliquer pour modifier votre email </p>
            """

            msg = EmailMessage(
                "Modification de mot de pass!",
                html,
                "oussoumanesow0@gmail.com",
                [user.email],
            )

            msg.content_subtype = 'html'
            msg.send()
            
            message = "processing forgot password"
            success = True
        else:
            print("user does not exist")
            error = True
            message = "user does not exist"
    
    context = {
        'success': success,
        'error':error,
        'message':message
    }
    return render(request, "authentification/forgot_password.html", context)


def update_password(request):
    return render(request, "authentification/update_password.html", {})


def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Votre mot de passe a été changé avec succès!')
            return redirect('profile')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'accounts/change_password.html', {'form': form})
##################################

def get_dec_reel_trim_value(instance):
    # Déterminer le trimestre actuel
    mois = date.today().month
    trimestre = (mois + 2) // 3  # 1 à 4

    # Construire dynamiquement le nom du champ
    field_name = f"dec_reel_t{trimestre}"

    # Utiliser getattr pour récupérer la valeur du champ
    return getattr(instance, field_name, None)


def get_dec_prev_trim_value(instance):
    # Déterminer le trimestre actuel
    mois = date.today().month
    trimestre = (mois + 2) // 3  # 1 à 4

    # Construire dynamiquement le nom du champ
    field_name = f"dec_prev_t{trimestre}"

    # Utiliser getattr pour récupérer la valeur du champ
    return getattr(instance, field_name, None)


def get_phy_reel_trim_value(instance):
    # Déterminer le trimestre actuel
    mois = date.today().month
    trimestre = (mois + 2) // 3  # 1 à 4

    # Construire dynamiquement le nom du champ
    field_name = f"realise_t{trimestre}_total"

    # Utiliser getattr pour récupérer la valeur du champ
    return getattr(instance, field_name, None)


def get_phy_prev_trim_value(instance):
    # Déterminer le trimestre actuel
    mois = date.today().month
    trimestre = (mois + 2) // 3  # 1 à 4

    # Construire dynamiquement le nom du champ
    field_name = f"prev_t{trimestre}_total"

    # Utiliser getattr pour récupérer la valeur du champ
    return getattr(instance, field_name, None)


def generate_decaissement_graph(selected_composante):
    # Préparer les données pour le graphique
    data = {
        'Trimestre': ['T1', 'T2', 'T3', 'T4'],
        'Réel': [
            selected_composante.dec_reel_t1,
            selected_composante.dec_reel_t2,
            selected_composante.dec_reel_t3,
            selected_composante.dec_reel_t4,
        ],
        'Prévisionnel': [
            selected_composante.dec_prev_t1,
            selected_composante.dec_prev_t2,
            selected_composante.dec_prev_t3,
            selected_composante.dec_prev_t4,
        ],
    }

    # Convertir les données en DataFrame
    df = pd.DataFrame(data)

    # Définir les couleurs personnalisées
    colors = {
        'Réel': '#004600',       # Bleu plus vif
        'Prévisionnel': '#8c8c8c' # Rouge-orangé
    }
    # Créer le graphique avec Plotly Express
    fig = px.line(
        df,
        x='Trimestre',
        y=['Réel', 'Prévisionnel'],
        markers=True,
        title=None,
        height=280,  # Hauteur réduite pour les petits espaces
        width=350,   # Largeur adaptée
        color_discrete_map=colors,  # Appliquer les couleurs personnalisées
    )

    # Personnaliser le graphique
    fig.update_layout(
        title=dict(
            text="Evolution du Décaissement",
            font=dict(size=20, family="Arial", color="#004466"),
            x=0.5,
            xanchor='center'
        ),
        xaxis_title="Trimestre",
        yaxis_title="Proportions",
        xaxis=dict(
            showgrid=False,
            tickfont=dict(size=8),
        ),
        yaxis=dict(
            gridcolor='lightgrey',
            tickfont=dict(size=8),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.3,
            xanchor="center",
            x=0.5,
            font=dict(size=8)   ,  # Réduire la taille de police
            itemwidth=40,  # Réduire la largeur des items de légende"
            title_text=None,
            
        ),
        template="plotly_white",
        margin=dict(t=0, b=20, l=20, r=20),
        plot_bgcolor="rgba(0,0,0,0)",
    )

    

    # Retourner le graphique sous forme de div HTML
    return plot(fig, include_plotlyjs=True, output_type='div')

def generate_physique_graph(selected_composante):  
    # Préparer les données pour le graphique
    data = {
        'Trimestre': ['T1', 'T2', 'T3', 'T4'],
        'Réel': [
            selected_composante.realise_t1_total,
            selected_composante.realise_t2_total,
            selected_composante.realise_t3_total,
            selected_composante.realise_t4_total,
        ],
        'Prévisionnel': [
            selected_composante.prev_t1_total,
            selected_composante.prev_t2_total,
            selected_composante.prev_t3_total,
            selected_composante.prev_t4_total,
        ],
    }

    # Convertir les données en DataFrame
    df = pd.DataFrame(data)

    # Définir les couleurs personnalisées
    colors = {
        'Réel': '#004600',       # Bleu plus vif
        'Prévisionnel': '#8c8c8c' # Rouge-orangé
    }
    # Créer le graphique avec Plotly Express
    fig = px.line(
        df,
        x='Trimestre',
        y=['Réel', 'Prévisionnel'],
        markers=True,
        title=None,
        height=280,  # Hauteur réduite pour les petits espaces
        width=350,   # Largeur adaptée
        color_discrete_map=colors,  # Appliquer les couleurs personnalisées
    )

    # Personnaliser le graphique
    fig.update_layout(
        title=dict(
            text="Evolution Physique",
            font=dict(size=20, family="Arial", color="#004466"),
            x=0.5,
            xanchor='center'
        ),
        xaxis_title="Trimestre",
        yaxis_title="Proportions",
        xaxis=dict(
            showgrid=False,
            tickfont=dict(size=8),
        ),
        yaxis=dict(
            gridcolor='lightgrey',
            tickfont=dict(size=8),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.3,
            xanchor="center",
            x=0.5,
            font=dict(size=8)   ,  # Réduire la taille de police
            itemwidth=40,  # Réduire la largeur des items de légende"
            title_text=None,
            
        ),
        template="plotly_white",
        margin=dict(t=0, b=20, l=20, r=20),
        plot_bgcolor="rgba(0,0,0,0)",
    )

    

    # Retourner le graphique sous forme de div HTML
    return plot(fig, include_plotlyjs=True, output_type='div')

## viewer
@login_required(login_url=reverse_lazy('sing_in'))
def dashboard_view(request):
    
    # Récupérer tous les ministères responsables distincts
    ministeres = Projet.objects.values_list('ministere_responsable', flat=True).distinct()
    map_html = None
    selected_ministere = request.GET.get('ministere', None)
    selected_composante = request.GET.get('composante', None)
    context = {
        'ministeres': ministeres,
        'selected_ministere': selected_ministere,
        'active_page': 'dashboard',
    }
    if selected_ministere:
        # Filtrer les projets par ministère sélectionné
        projets = Projet.objects.filter(ministere_responsable=selected_ministere)
        
        # Nombre total de projets pour ce ministère
        nb_projets = projets.count()
        
        # Nombre de projets lancés
        nb_projets_lances = projets.filter(est_lance=True).count()
        
        # Trouver les programmes associés à ces projets
        programme_ids = projets.values_list('programme_id', flat=True).distinct()
        programmes = Programme.objects.filter(id__in=programme_ids)
        nb_programmes = programmes.count()
        
        # Trouver les portefeuilles associés à ces programmes
        portefeuille_ids = programmes.values_list('portefeuille_id', flat=True).distinct()
        portefeuilles = Portefeuille.objects.filter(id__in=portefeuille_ids)
        
        # Récupérer les responsables de portefeuille
        responsables_portefeuille = list(portefeuilles.values('responsable'))

        # recuperer les noms des axes associes aux portefeuilles
        axes = Axe.objects.filter(id__in=portefeuilles.values_list('axe_id', flat=True))

        
        context.update({
            'nb_projets': nb_projets,
            'nb_projets_lances': nb_projets_lances,
            'nb_programmes': nb_programmes,
            'responsables_portefeuille': responsables_portefeuille,
            'axes': axes,
            'portefeuilles': portefeuilles,
            'programmes': programmes,
        })


        # Filtrer par programme sélectionné
        selected_programme_id = request.GET.get('programme', None)
        if selected_programme_id:
            selected_programme = Programme.objects.get(id=selected_programme_id)
            projets = projets.filter(programme=selected_programme)
            context.update({
                'projets': projets,
                'programmes': programmes,
                'selected_programme': selected_programme,
            })


            selected_projet_id = request.GET.get('projet', None)
            if selected_projet_id:
                selected_projet = Projet.objects.get(id=selected_projet_id)
                composantes = selected_projet.composante_set.all()

                # nombre de composantes dans le projet
                nb_composantes = projets.values_list('composante__id', flat=True).distinct().count()
                # nom chef projet
                chef_projet = selected_projet.chef_projet
                # email chef projet
                email_chef_projet = selected_projet.email
                # tel chef projet
                tel_chef_projet = selected_projet.tel
                # nombre de composantes en cours
                composantes = selected_projet.composante_set.all()
                nb_composantes_ouvertes = composantes.filter(statut='En cours').count()
                nb_composantes_terminees = composantes.filter(statut='Terminée').count()
                nb_composantes_bloquees = composantes.filter(statut='Bloquée').count()
                nb_composantes_depriorisees = composantes.filter(statut='Dépriorisée').count()

                # gauge plotly pour le nombre de composantes bloquées
                fig_nb_composantes_bloquees = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=nb_composantes_bloquees,
                    gauge={'axis': {'range': [0, nb_composantes]}},
                ))

                fig_nb_composantes_bloquees.update_layout(
                    autosize=False,
                    width=200,   # adapte selon la taille de ta colonne
                    height=200,  # ou 150 selon ton besoin
                    margin=dict(l=10, r=10, t=0, b=10),
                )

                #gauge plotly pour le nombre de composantes ouvertes
                fig_nb_composantes_ouvertes = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=nb_composantes_ouvertes,
                    gauge={'axis': {'range': [0, nb_composantes]}},
                ))

                fig_nb_composantes_ouvertes.update_layout(
                    autosize=False,
                    width=200,   # adapte selon la taille de ta colonne
                    height=200,  # ou 150 selon ton besoin
                    margin=dict(l=10, r=10, t=0, b=10),
                )

                #gauge plotly pour le nombre de composantes dépriorisées
                fig_nb_composantes_depriorisees = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=nb_composantes_depriorisees,
                    gauge={'axis': {'range': [0, nb_composantes]}},
                ))

                fig_nb_composantes_depriorisees.update_layout(
                    autosize=False,
                    width=200,   # adapte selon la taille de ta colonne
                    height=200,  # ou 150 selon ton besoin
                    margin=dict(l=10, r=10, t=0, b=10),
                )

                context.update({
                    'selected_projet': selected_projet,
                    'nb_composantes': nb_composantes,
                    'chef_projet': chef_projet, 
                    'email_chef_projet': email_chef_projet,
                    'tel_chef_projet': tel_chef_projet,
                    'projets': projets,
                    'composantes': composantes,
                    'nb_composantes_ouvertes': nb_composantes_ouvertes,
                    'nb_composantes_terminees': nb_composantes_terminees, 
                    'nb_composantes_bloquees': nb_composantes_bloquees,
                    'nb_composantes_depriorisees': nb_composantes_depriorisees,
                    'fig_nb_composantes_bloquees': plot(fig_nb_composantes_bloquees, include_plotlyjs=False, output_type='div'),
                    'fig_nb_composantes_ouvertes': plot(fig_nb_composantes_ouvertes, include_plotlyjs=False, output_type='div'),
                    'fig_nb_composantes_depriorisees': plot(fig_nb_composantes_depriorisees, include_plotlyjs=False, output_type='div'),
                })

                # Filtrer par composante sélectionnée
                selected_composante_id = request.GET.get('composante', None)
                if selected_composante_id:
                    selected_composante = Composante.objects.get(id=selected_composante_id)
                    # la partie 1
                    nom_composante = selected_composante.nom
                    statut_composante = selected_composante.statut
                    date_lancement = selected_composante.date_lancement 
                    agence_execution = selected_composante.agence_execution
                    ministere_mise_en_oeuvre = selected_composante.tutelle
                    financement = selected_composante.cout
                    partenaire_pad = selected_composante.partenaire_pad
                    localisation = selected_composante.localisation

                    # la partie 2 : Avancement du projet
                    obj = Composante.objects.get(id=1)
                    dec_reel = get_dec_reel_trim_value(obj)
                    dec_prev = get_dec_prev_trim_value(obj)
                    dec_cible = selected_composante.dec_cible
                    taux_decaissement = selected_composante.taux_decaissement
                    phy_reel = get_phy_reel_trim_value(obj)
                    phy_prev = get_phy_prev_trim_value(obj)
                    phys_cible = selected_composante.cible_total
                    avancement_physique = selected_composante.avancement_physique_total


                    decaissement_graph = generate_decaissement_graph(selected_composante)
                    physique_graph = generate_physique_graph(selected_composante)
                    # Les problèmes rencontrés
                    problemes = selected_composante.probleme_set.all()
                    # Créer la carte pour la région de la composante
                    map_html = create_map_for_region(selected_composante.localisation)


                    context.update({
                        'selected_composante': selected_composante,
                        'nom_composante': nom_composante,
                        'statut_composante': statut_composante,
                        'date_lancement': date_lancement,
                        'agence_execution': agence_execution,
                        'ministere_mise_en_oeuvre': ministere_mise_en_oeuvre,
                        'financement': financement,
                        'partenaire_pad': partenaire_pad,
                        'localisation': localisation,
                        'dec_reel': dec_reel,
                        'dec_prev': dec_prev,
                        'dec_cible': dec_cible,
                        'taux_decaissement': taux_decaissement,
                        'phy_reel': phy_reel,
                        'phy_prev': phy_prev,
                        'phys_cible': phys_cible,
                        'avancement_physique': avancement_physique,
                        'problemes': problemes,
                        'decaissement_graph': decaissement_graph,
                        'physique_graph': physique_graph,
                        'map_html': map_html,
                    })


    return render(request, 'dashboard_app/dashboard.html', context)

## viewer

@login_required(login_url=reverse_lazy('sing_in'))
def dashboard_coordo_view(request):
    context ={
        'active_page': 'dashboard_coordo',
    }
    return render(request, 'dashboard_app/dashboard_coordo.html', context)

def data_get_view(request):
    
    # user = request.user

    #if user.is_authenticated and user.role == 'gestionnaire':
    #    Portefeuilles= Portefeuille.objects.filter(responsable=user)
    #    Programmes= Programme.objects.filter(portefeuille__responsable=user)
    #    Projets= Projet.objects.filter(programme__portefeuille__responsable=user)
    #    Composantes= Composante.objects.filter(projet__programme__portefeuille__responsable=user)
    #    Activites= Activite.objects.filter(composante__projet__programme__portefeuille__responsable=user)
    #    Problemes= Probleme.objects.filter(activite__composante__projet__programme__portefeuille__responsable=user)
    #    Messages_week=Message.objects.filter(activite__composante__projet__programme__portefeuille__responsable=user)
    #    Axes= Axe.objects.all()
    #else:
    Axes = Axe.objects.all()
    Portefeuilles = Portefeuille.objects.all()
    Programmes = Programme.objects.all()
    Projets = Projet.objects.all()
    Composantes = Composante.objects.all()
    Activites = Activite.objects.all()
    Problemes = Probleme.objects.all()
    Messages_week = Message.objects.all()

    
    ministeres = Projet.objects.values_list('ministere_responsable', flat=True).distinct()
    # Sérialiser les données en incluant les propriétés calculées pour les composantes
    composantes_data = []
    for composante in Composantes:
        composante_dict = {
            'id': composante.id,
            'projet_id': composante.projet_id,
            'nom': composante.nom,
            'identifiant': composante.identifiant,
            'localisation': composante.localisation,
            'tutelle': composante.tutelle,
            'agence_execution': composante.agence_execution,
            'date_lancement': composante.date_lancement.strftime('%Y-%m-%d') if composante.date_lancement else None,
            'Fin_previsionnelle': composante.Fin_previsionnelle.strftime('%Y-%m-%d') if composante.Fin_previsionnelle else None,
            'duree_mois': composante.duree_mois,
            'cout': float(composante.cout) if composante.cout else None,
            'statut': composante.statut,
            'partenaire_pad': composante.partenaire_pad,
            'facteurs_explication': composante.facteurs_explication,
            'etat':composante.etat,
            # Décaissement
            'dec_prev_t1': float(composante.dec_prev_t1) if composante.dec_prev_t1 else None,
            'dec_prev_t2': float(composante.dec_prev_t2) if composante.dec_prev_t2 else None,
            'dec_prev_t3': float(composante.dec_prev_t3) if composante.dec_prev_t3 else None,
            'dec_prev_t4': float(composante.dec_prev_t4) if composante.dec_prev_t4 else None,
            'dec_cible': float(composante.dec_cible) if composante.dec_cible else None,
            'dec_reel_t1': float(composante.dec_reel_t1) if composante.dec_reel_t1 else None,
            'dec_reel_t2': float(composante.dec_reel_t2) if composante.dec_reel_t2 else None,
            'dec_reel_t3': float(composante.dec_reel_t3) if composante.dec_reel_t3 else None,
            'dec_reel_t4': float(composante.dec_reel_t4) if composante.dec_reel_t4 else None,
            'taux_decaissement': float(composante.taux_decaissement) if composante.taux_decaissement else None,
            
            # Ajouter les propriétés calculées ici
            'prev_t1_total': float(composante.prev_t1_total) if composante.prev_t1_total is not None else None,
            'prev_t2_total': float(composante.prev_t2_total) if composante.prev_t2_total is not None else None,
            'prev_t3_total': float(composante.prev_t3_total) if composante.prev_t3_total is not None else None,
            'prev_t4_total': float(composante.prev_t4_total) if composante.prev_t4_total is not None else None,
            'cible_total': float(composante.cible_total) if composante.cible_total is not None else None,
            'realise_t1_total': float(composante.realise_t1_total) if composante.realise_t1_total is not None else None,
            'realise_t2_total': float(composante.realise_t2_total) if composante.realise_t2_total is not None else None,
            'realise_t3_total': float(composante.realise_t3_total) if composante.realise_t3_total is not None else None,
            'realise_t4_total': float(composante.realise_t4_total) if composante.realise_t4_total is not None else None,
            'avancement_physique_total': float(composante.avancement_physique_total) if composante.avancement_physique_total is not None else None,
        }
        composantes_data.append(composante_dict)

    return  JsonResponse({
        'Axes': list(Axes.values()),
        'Portefeuilles': [
            {
                'id': p.id,
                'nom': p.nom,
                'responsable': p.responsable.nom if p.responsable else None,
                'axe_id': p.axe_id,
            }
            for p in Portefeuilles
        ],
        'Programmes': list(Programmes.values()),
        'Projets': list(Projets.values()),
        'Composantes': composantes_data,
        'Activites': list(Activites.values()),
        'Problemes': list(Problemes.values()),
        'ministeres': list(ministeres.values()),
        'Messages_week' : list(Messages_week.values())
    })


## viewer
@login_required(login_url=reverse_lazy('sing_in'))
def create_map_for_region(region_name):
    """Crée une carte folium avec la région spécifiée mise en évidence"""
    # Créer une carte centrée sur le Sénégal
    m = folium.Map(location=[14.4974, -14.4524], zoom_start=7)
    
    # Charger les données GeoJSON pour les régions du Sénégal
    try:
        geojson_path = Path(settings.STATICFILES_DIRS[0]) / "assets"/ "data" / "senegal_regions.json"
    
        # Vérifier si le fichier existe
        print(f"Vérification du fichier GeoJSON : {geojson_path}")
        if not geojson_path.is_file():
            raise FileNotFoundError(f"Fichier GeoJSON introuvable: {geojson_path}")
        
        with open(geojson_path, 'r', encoding='utf-8') as f:
            senegal_regions = json.load(f)
            print("Fichier GeoJSON chargé avec succès.")
        
        # Vérification de la présence de la région
        region_names = [feature['properties']['NAME_1'] for feature in senegal_regions['features']]
        print(f"Régions disponibles : {region_names}")
        
        # Style par défaut et style pour la région sélectionnée
        def style_function(feature):
            if feature['properties']['NAME_1'] == region_name:
                return {
                    'fillColor': '#004600',  # vers bocs
                    'color': 'black',
                    'weight': 2,
                    'fillOpacity': 1
                }
            else:
                return {
                    'fillColor': '#ffffff',  # blanc
                    'color': '#004600',
                    'weight': 1,
                    'fillOpacity': 1
                }
        
        # Ajouter la couche GeoJSON à la carte
        folium.GeoJson(
            senegal_regions,
            name='regions',
            style_function=style_function,
            tooltip=folium.features.GeoJsonTooltip(
                fields=['NAME_1'],
                aliases=['Région:'],
                localize=True
            )
        ).add_to(m)
        
        # Ajouter un titre
        title_html = '''
            <div style="position: fixed; 
                        top: 10px; left: 50px; width: 300px; 
                        z-index:1000; background-color: white; padding: 10px;
                        border-radius: 5px; box-shadow: 0 0 5px rgba(0,0,0,0.3);">
                <h4 style="margin: 0; font-size: 16px;">Zone d'intervention: <b>{}</b></h4>
            </div>
        '''.format(region_name)
        m.get_root().html.add_child(folium.Element(title_html))
        
        # Convertir la carte en HTML
        return m._repr_html_()
    
    except FileNotFoundError as e:
        print(f"Erreur : {e}")
        return "<div>Erreur : fichier GeoJSON introuvable.</div>"
    except Exception as e:
        print(f"Erreur lors de la création de la carte: {e}")
        return "<div>Erreur lors du chargement de la carte</div>"


def home_view(request):
    return render(request, 'dashboard_app/home.html')


def table_view(request):
    context = {
        'active_page': 'tables'
    }
    return render(request, 'dashboard_app/tables.html', context)


## viewer


def notification_view(request):
    context = {
        'active_page': 'notifications'
    }
    return render(request, 'dashboard_app/notifications.html', context) 

## viewer
@login_required(login_url=reverse_lazy('sing_in'))
def profile_view(request):
    password_form = PasswordChangeForm(request.user)
    
    if request.method == 'POST' and 'change_password' in request.POST:
        password_form = PasswordChangeForm(request.user, request.POST)
        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)  # Important pour ne pas déconnecter l'utilisateur
            messages.success(request, 'Votre mot de passe a été changé avec succès!')
            return redirect('profile')
    context = {
        'password_form': password_form,
        'active_page': 'profile'
    }
    return render(request, 'authentification/profile.html', context)
## viewer
@login_required(login_url=reverse_lazy('sing_in'))
def base_view(request):
    return render(request, 'dashboard_app/base.html') # Render the base.html template

## viewer
@login_required(login_url=reverse_lazy('sing_in'))
def menu_view(request):
    return render(request, 'dashboard_app/menu.html') # Render the menu.html template


def get_changes_for_history(history_queryset):
    history = list(history_queryset)
    changes = []

    # Créer une version précédente pour chaque version courante
    for current, previous in zip(history, history[1:] + [None]):
        if previous is None:
            changes.append((current, []))
        else:
            delta = current.diff_against(previous)
            field_changes = [
                {
                    'field': change.field,
                    'old': change.old,
                    'new': change.new
                }
                for change in delta.changes
            ]
            changes.append((current, field_changes))
    return changes


## viewer
@login_required(login_url=reverse_lazy('sing_in'))
def projets_data_view(request):
    programmes = Programme.objects.all()
    projets = Projet.objects.all().select_related('programme')
    
     # Récupérer les historiques triés
    historiques_prj_raw = list(Projet.history.all().order_by('-history_date'))
    
    # Récupérer les changements
    historiques_prj = get_changes_for_history(historiques_prj_raw)

    # Récupérer les ministères uniques
    ministeres_uniques = Projet.objects.values_list('ministere_responsable', flat=True).distinct()
    return render(request, 'tables/projet.html', {
        'active_page': 'tables_sub1',
        'Projets': projets,
        'Programmes': programmes,
        'ministeres_uniques': ministeres_uniques,
        'historiques_prj' : historiques_prj
    })



## viewer
@login_required(login_url=reverse_lazy('sing_in'))
def composantes_data_view(request):
    projets = Projet.objects.all()
    composantes=Composante.objects.all().select_related('projet')

     # Récupérer les historiques triés
    historiques_compo_raw = list(Composante.history.all().order_by('-history_date'))
    
    # Récupérer les changements
    historiques_compo = get_changes_for_history(historiques_compo_raw)

    return render(request, 'tables/composante.html', {
        'active_page': 'tables_sub2', 
        'Projets': projets,
        'Composantes': composantes,
        'historiques_compo':historiques_compo,
    })


## viewer
@login_required(login_url=reverse_lazy('sing_in'))
def activites_data_view(request):
    
    composantes = Composante.objects.all()
    activites=Activite.objects.all().select_related('composante')

     # Récupérer les historiques triés
    historiques_activite_raw = list(Activite.history.all().order_by('-history_date'))
    
    # Récupérer les changements
    historiques_activite = get_changes_for_history(historiques_activite_raw)
    return render(request, 'tables/activites.html', {
        'active_page': 'tables_sub3',
        'Activites': activites,
        'Composantes': composantes,
        'historiques_activite' : historiques_activite,
    })


## viewer
@login_required(login_url=reverse_lazy('sing_in'))
def problemes_data_view(request):
    
    composantes = Composante.objects.all()
    problemes=Probleme.objects.all().select_related('composante')

    
    
    # Récupérer les historiques triés
    historiques_probleme_raw = list(Probleme.history.all().order_by('-history_date'))
    
    # Récupérer les changements
    historiques_probleme = get_changes_for_history(historiques_probleme_raw)

    return render(request, 'tables/probleme.html', {
        'active_page': 'tables_sub4',
        'Problemes': problemes,
        'Composantes': composantes,
        'historiques_probleme' : historiques_probleme,
    })


## viewer
@login_required(login_url=reverse_lazy('sing_in'))
def messages_data_view(request):
    
    composantes = Composante.objects.all()
    messages=Message.objects.all().select_related('composante')

    
    # Récupérer les historiques triés
    historiques_message_raw = list(Message.history.all().order_by('-history_date'))
    
    # Récupérer les changements
    historiques_message = get_changes_for_history(historiques_message_raw)

    return render(request, 'tables/message.html', {
        'active_page': 'tables_sub5',
        'Messages': messages,
        'Composantes': composantes,
        'historiques_probleme' : historiques_message,
    })





class UploadUnifiedCSVForm(Form):
    csv_file = FileField(label="Fichier CSV unifié")

def parse_date(date_str):
    """Parse une date à partir d'une chaîne de caractères."""
    if not date_str or date_str.strip() == '':
        return None
    
    date_formats = [
        "%Y-%m-%d",  # Format ISO (standard)
        "%d/%m/%Y",  # Format français
        "%m/%d/%Y",  # Format américain (ton cas)
        "%d-%m-%Y",  # Variante
        "%m-%d-%Y",  # Variante américaine
    ]
    
    for date_format in date_formats:
        try:
            return datetime.strptime(date_str.strip(), date_format).date()
        except ValueError:
            continue
    
    raise ValueError(f"Format de date non reconnu: {date_str}")

def parse_decimal(value):
    """Convertit une chaîne en décimal."""
    if not value or value.strip() == '':
        return None
    return Decimal(value.replace(',', '.'))

def parse_boolean(value):
    """Convertit une chaîne en booléen."""
    if not value or value.strip() == '':
        return False
    return value.lower() in ('true', 'oui', 'yes', '1')

## viewer
@login_required(login_url=reverse_lazy('sing_in'))
def import_csv_projets(request):
    """Importe toutes les données à partir d'un seul fichier CSV."""
    if request.method == 'POST':
        form = UploadUnifiedCSVForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = TextIOWrapper(request.FILES['csv_file'].file, encoding='utf-8')
            reader = csv.DictReader(csv_file)
            
            # Statistiques d'importation
            stats = {
                'axes': {'created': 0, 'updated': 0, 'errors': []},
                'portefeuilles': {'created': 0, 'updated': 0, 'errors': []},
                'programmes': {'created': 0, 'updated': 0, 'errors': []},
                'projets': {'created': 0, 'updated': 0, 'errors': []},
                'composantes': {'created': 0, 'updated': 0, 'errors': []}
            }
            
            # Dictionnaires pour stocker les références entre objets
            axes_dict = {}
            portefeuilles_dict = {}
            programmes_dict = {}
            projets_dict = {}
            
            # Parcourir le CSV
            for row_num, row in enumerate(reader, start=2):
                try:
                    # 1. Traiter l'Axe
                    axe_nom = row.get('axe_nom', '').strip()
                    if axe_nom:
                        if axe_nom not in axes_dict:
                            axe, created = Axe.objects.get_or_create(nom=axe_nom)
                            axes_dict[axe_nom] = axe
                            if created:
                                stats['axes']['created'] += 1
                            else:
                                stats['axes']['updated'] += 1
                        
                        axe = axes_dict[axe_nom]
                    else:
                        axe = None
                    
                    # 2. Traiter le Portefeuille
                    portefeuille_nom = row.get('portefeuille_nom', '').strip()
                    portefeuille_responsable = row.get('portefeuille_responsable', '').strip()

                    if portefeuille_nom and axe:
                        if portefeuille_nom not in portefeuilles_dict:
                            try:
                                # Récupérer ou créer automatiquement un utilisateur gestionnaire
                                user_responsable, user_created = CustomUser.objects.get_or_create(
                                    nom=portefeuille_responsable,
                                    defaults={
                                        'username': portefeuille_responsable.lower().replace(' ', '_'),
                                        'role': 'gestionnaire',
                                        'password': CustomUser.objects.make_random_password()
                                    }
                                )

                                portefeuille, created = Portefeuille.objects.get_or_create(
                                    nom=portefeuille_nom,
                                    defaults={
                                        'responsable': user_responsable,
                                        'axe': axe
                                    }
                                )

                                if not created:
                                    portefeuille.responsable = user_responsable
                                    portefeuille.axe = axe
                                    portefeuille.save()
                                    stats['portefeuilles']['updated'] += 1
                                else:
                                    stats['portefeuilles']['created'] += 1

                                if user_created:
                                    messages.info(request, f"Utilisateur '{portefeuille_responsable}' créé automatiquement avec succès.")

                                portefeuilles_dict[portefeuille_nom] = portefeuille

                            except Exception as e:
                                stats['portefeuilles']['errors'].append(f"Ligne {row_num}: Erreur portefeuille - {str(e)}")
                                portefeuille = None
                        else:
                            portefeuille = portefeuilles_dict[portefeuille_nom]
                    else:
                        portefeuille = None
                    
                    # 3. Traiter le Programme
                    programme_id = row.get('programme_id', '').strip()
                    programme_nom = row.get('programme_nom', '').strip()
                    
                    if programme_id and programme_nom and axe:
                        if programme_id not in programmes_dict:
                            programme, created = Programme.objects.get_or_create(
                                identifiant=programme_id,
                                defaults={
                                    'nom': programme_nom,
                                    'axe': axe,
                                    'portefeuille': portefeuille
                                }
                            )
                            
                            if not created:
                                programme.nom = programme_nom
                                programme.axe = axe
                                programme.portefeuille = portefeuille
                                programme.save()
                                stats['programmes']['updated'] += 1
                            else:
                                stats['programmes']['created'] += 1
                                
                            programmes_dict[programme_id] = programme
                        
                        programme = programmes_dict[programme_id]
                    else:
                        programme = None
                    
                    # 4. Traiter le Projet
                    projet_id = row.get('projet_id', '').strip()
                    projet_nom = row.get('projet_nom', '').strip()
                    
                    if projet_id and projet_nom and programme:
                        if projet_id not in projets_dict:
                            est_lance = parse_boolean(row.get('projet_est_lance', 'False'))
                            ministere_responsable = row.get('projet_ministere_responsable', '').strip()
                            chef_projet = row.get('projet_chef_projet', '').strip()
                            email = row.get('projet_email', '').strip()
                            tel = row.get('projet_tel', '').strip()
                            
                            projet, created = Projet.objects.get_or_create(
                                identifiant=projet_id,
                                defaults={
                                    'nom': projet_nom,
                                    'programme': programme,
                                    'est_lance': est_lance,
                                    'ministere_responsable': ministere_responsable,
                                    'chef_projet': chef_projet,
                                    'email': email,
                                    'tel': tel
                                }
                            )
                            
                            if not created:
                                projet.nom = projet_nom
                                projet.programme = programme
                                projet.est_lance = est_lance
                                projet.ministere_responsable = ministere_responsable
                                projet.chef_projet = chef_projet
                                projet.email = email
                                projet.tel = tel
                                projet.save()
                                stats['projets']['updated'] += 1
                            else:
                                stats['projets']['created'] += 1
                                
                            projets_dict[projet_id] = projet
                        
                        projet = projets_dict[projet_id]
                    else:
                        projet = None
                    
                    # 5. Traiter la Composante
                    composante_id = row.get('composante_id', '').strip()
                    composante_nom = row.get('composante_nom', '').strip()
                    
                    if composante_id and composante_nom and projet:
                        # Récupérer les données de la composante
                        localisation = row.get('composante_localisation', '').strip()
                        tutelle = row.get('composante_tutelle', '').strip()
                        agence_execution = row.get('composante_agence_execution', '').strip()
                        date_lancement = parse_date(row.get('composante_date_lancement', ''))
                        Fin_previsionnelle = parse_date(row.get('composante_fin_previsionnelle', ''))
                        duree_mois = int(row.get('composante_duree_mois', 0)) if row.get('composante_duree_mois') else None
                        cout = parse_decimal(row.get('composante_cout', ''))
                        statut = row.get('composante_statut', '').strip()
                        etat = row.get('composante_etat', '').strip()
                        
                        # Financements
                        financement_public = parse_decimal(row.get('composante_financement_public', ''))
                        financement_prive = parse_decimal(row.get('composante_financement_prive', ''))
                        financement_ppp = parse_decimal(row.get('composante_financement_ppp', ''))
                        
                        # Décaissements
                        dec_prev_t1 = parse_decimal(row.get('composante_dec_prev_t1', ''))
                        dec_prev_t2 = parse_decimal(row.get('composante_dec_prev_t2', ''))
                        dec_prev_t3 = parse_decimal(row.get('composante_dec_prev_t3', ''))
                        dec_prev_t4 = parse_decimal(row.get('composante_dec_prev_t4', ''))
                        dec_cible = parse_decimal(row.get('composante_dec_cible', ''))
                        dec_reel_t1 = parse_decimal(row.get('composante_dec_reel_t1', ''))
                        dec_reel_t2 = parse_decimal(row.get('composante_dec_reel_t2', ''))
                        dec_reel_t3 = parse_decimal(row.get('composante_dec_reel_t3', ''))
                        dec_reel_t4 = parse_decimal(row.get('composante_dec_reel_t4', ''))
                        taux_decaissement = parse_decimal(row.get('composante_taux_decaissement', ''))
                        facteurs_explication = row.get('composante_facteurs_explication', '')
                        partenariat_pad = row.get('composante_partenaire_pad', '').strip()
                        
                        # Vérifier que la somme des financements est égale à 100%
                        financement_total = (financement_public or 0) + (financement_prive or 0) + (financement_ppp or 0)
                        if financement_total > 0 and financement_total != 100:
                            raise ValidationError(f"La somme des pourcentages de financement doit être égale à 100%. Actuellement: {financement_total}%")
                        
                        composante, created = Composante.objects.get_or_create(
                            identifiant=composante_id,
                            defaults={
                                'nom': composante_nom,
                                'projet': projet,
                                'localisation': localisation,
                                'tutelle': tutelle,
                                'agence_execution': agence_execution,
                                'date_lancement': date_lancement,
                                'duree_mois': duree_mois,
                                'cout': cout,
                                'statut': statut,
                                'etat': etat,
                                'financement_public': financement_public,
                                'financement_prive': financement_prive,
                                'financement_ppp': financement_ppp,
                                'dec_prev_t1': dec_prev_t1,
                                'dec_prev_t2': dec_prev_t2,
                                'dec_prev_t3': dec_prev_t3,
                                'dec_prev_t4': dec_prev_t4,
                                'dec_cible': dec_cible,
                                'dec_reel_t1': dec_reel_t1,
                                'dec_reel_t2': dec_reel_t2,
                                'dec_reel_t3': dec_reel_t3,
                                'dec_reel_t4': dec_reel_t4,
                                'taux_decaissement': taux_decaissement,
                                'facteurs_explication': facteurs_explication,
                                'Fin_previsionnelle': Fin_previsionnelle,
                                'partenariat_pad': partenariat_pad,
                            }
                        )
                        
                        if not created:
                            composante.nom = composante_nom
                            composante.projet = projet
                            composante.localisation = localisation
                            composante.tutelle = tutelle
                            composante.agence_execution = agence_execution
                            composante.date_lancement = date_lancement
                            composante.duree_mois = duree_mois
                            composante.cout = cout
                            composante.statut = statut
                            composante.etat = etat
                            composante.financement_public = financement_public
                            composante.financement_prive = financement_prive
                            composante.financement_ppp = financement_ppp
                            composante.dec_prev_t1 = dec_prev_t1
                            composante.dec_prev_t2 = dec_prev_t2
                            composante.dec_prev_t3 = dec_prev_t3
                            composante.dec_prev_t4 = dec_prev_t4
                            composante.dec_cible = dec_cible
                            composante.dec_reel_t1 = dec_reel_t1
                            composante.dec_reel_t2 = dec_reel_t2
                            composante.dec_reel_t3 = dec_reel_t3
                            composante.dec_reel_t4 = dec_reel_t4
                            composante.taux_decaissement = taux_decaissement
                            composante.facteurs_explication = facteurs_explication
                            composante.Fin_previsionnelle = Fin_previsionnelle
                            composante.partenaire_pad = partenariat_pad
                            composante.save()
                            stats['composantes']['updated'] += 1
                        else:
                            stats['composantes']['created'] += 1
                
                except Exception as e:
                    error_msg = f"Ligne {row_num}: {str(e)}"
                    # Déterminer à quelle entité attribuer l'erreur
                    if 'composante' in str(e).lower():
                        stats['composantes']['errors'].append(error_msg)
                    elif 'projet' in str(e).lower():
                        stats['projets']['errors'].append(error_msg)
                    elif 'programme' in str(e).lower():
                        stats['programmes']['errors'].append(error_msg)
                    elif 'portefeuille' in str(e).lower():
                        stats['portefeuilles']['errors'].append(error_msg)
                    elif 'axe' in str(e).lower():
                        stats['axes']['errors'].append(error_msg)
                    else:
                        # Si on ne peut pas déterminer, on l'ajoute à composantes (niveau le plus bas)
                        stats['composantes']['errors'].append(error_msg)
            
            # Afficher les messages de succès et d'erreur
            for entity, data in stats.items():
                if data['created'] > 0:
                    messages.success(request, f"{data['created']} {entity} créé(s) avec succès.")
                if data['updated'] > 0:
                    messages.info(request, f"{data['updated']} {entity} mis à jour.")
                if data['errors']:
                    messages.error(request, f"{len(data['errors'])} erreurs pour {entity}: {' | '.join(data['errors'][:3])}" + ("..." if len(data['errors']) > 3 else ""))
            
            
    else:
        form = UploadUnifiedCSVForm()
    
    return render(request, 'tables/import_projet.html', {'form': form})

## viewer
@login_required(login_url=reverse_lazy('sing_in'))
def ajouter_projet(request):
    ajoutprojetform=ProjetForm()
    if request.method=='POST':
        ajoutprojetform=ProjetForm(request.POST)
        if ajoutprojetform.is_valid():
            ajoutprojetform.save()
            return redirect('/tables/projets')
    context={'form': ajoutprojetform}
    return render(request, 'tables/Ajout_projet.html', context)

## viewer
@login_required(login_url=reverse_lazy('sing_in'))
def modifie_projet(request, pk):
    projet=Projet.objects.get(id=pk)
    modifieprojetform=ProjetForm(instance=projet)
    if request.method=='POST':
        modifieprojetform=ProjetForm(request.POST, instance=projet)
        if modifieprojetform.is_valid():
            modifieprojetform.save()
            return redirect('/tables/projets')
    context={'form': modifieprojetform}
    return render(request, 'tables/Ajout_projet.html', context)

def supprimer_projet(request, pk):
    projet = get_object_or_404(Projet, pk=pk)
    projet.delete()
    messages.success(request, "Le projet a été supprimé avec succès.")
    return redirect('tables_sub1')


## viewer
@login_required(login_url=reverse_lazy('sing_in'))
def import_csv_activite(request):
    if request.method == 'POST':
        form = UploadCSVForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = TextIOWrapper(request.FILES['csv_file'].file, encoding='utf-8')
            reader = csv.DictReader(csv_file)
            
            success_count = 0
            errors = []
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    # Récupérer la composante
                    composante_nom = row.get('composante', '').strip()
                    if not composante_nom:
                        raise ValidationError("Le nom de la composante est requis")
                    
                    try:
                        composante = Composante.objects.get(nom=composante_nom)
                    except ObjectDoesNotExist:
                        raise ValidationError(f"La composante '{composante_nom}' n'existe pas")
                    
                    # Créer le problème
                    Activite.objects.create(
                        composante=composante,
                        identifiant=row.get('identifiant', ''),
                        nom=row.get('nom', ''),
                        ponderation=row.get('ponderation', ''),
                        prev_t1=row.get('prev_t1', ''),
                        prev_t2=row.get('prev_t2', ''),
                        prev_t3=row.get('prev_t3', ''),
                        prev_t4=row.get('prev_t4', ''),
                        cible_fin_annee=row.get('cible_fin_annee', ''),
                        realise_t1=row.get('realise_t1', ''),
                        realise_t2=row.get('realise_t2', ''),
                        realise_t3=row.get('realise_t3', ''),
                        realise_t4=row.get('realise_t4', ''),
                        avancement_physique=row.get('avancement_physique', ''),
                    )
                    success_count += 1
                    
                except Exception as e:
                    errors.append(f"Ligne {row_num}: {str(e)}")
            
            if success_count > 0:
                messages.success(request, f"{success_count} activités importées avec succès!")
            if errors:
                messages.error(request, f"Erreurs sur {len(errors)} lignes. {' | '.join(errors[:3])}" + ("..." if len(errors)>3 else ""))
            
            #return redirect('tables/problemes/import-csv/')
    else:
        form = UploadCSVForm()
    
    return render(request, 'tables/import_activite.html', {'form': form})


## viewer
@login_required(login_url=reverse_lazy('sing_in'))
def ajouter_activite(request):
    ajoutactiviteform=ActiviteForm()
    if request.method=='POST':
        ajoutactiviteform=ActiviteForm(request.POST)
        if ajoutactiviteform.is_valid():
            ajoutactiviteform.save()
            return redirect('/tables/activites')
    context={'form': ajoutactiviteform}
    return render(request, 'tables/Ajout_activite.html', context)

## viewer
@login_required(login_url=reverse_lazy('sing_in'))
def modifie_activite(request, rk):
    activite=Activite.objects.get(id=rk)
    modifieactiviteform=ActiviteForm(instance=activite)
    if request.method=='POST':
        modifieactiviteform=ActiviteForm(request.POST, instance=activite)
        if modifieactiviteform.is_valid():
            modifieactiviteform.save()
            return redirect('/tables/activites')
    context={'form': modifieactiviteform}
    return render(request, 'tables/Ajout_activite.html', context)

def supprimer_activite(request, pk):
    activite = get_object_or_404(Activite, pk=pk)
    activite.delete()
    messages.success(request, "L'activité a été supprimée avec succès.")
    return redirect('tables_sub3')


## viewer
@login_required(login_url=reverse_lazy('sing_in'))
def import_csv_problem(request):
    if request.method == 'POST':
        form = UploadCSVForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = TextIOWrapper(request.FILES['csv_file'].file, encoding='utf-8')
            reader = csv.DictReader(csv_file)
            
            success_count = 0
            errors = []
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    # Récupérer la composante
                    composante_nom = row.get('composante', '').strip()
                    if not composante_nom:
                        raise ValidationError("Le nom de la composante est requis")
                    
                    try:
                        composante = Composante.objects.get(nom=composante_nom)
                    except ObjectDoesNotExist:
                        raise ValidationError(f"La composante '{composante_nom}' n'existe pas")
                    
                    # Créer le problème
                    Probleme.objects.create(
                        composante=composante,
                        identifiant=row.get('identifiant', ''),
                        titre=row.get('titre', ''),
                        description=row.get('description', ''),
                        date_identification=parse_date(row.get('date_identification')),
                        source=row.get('source', ''),
                        typologie=row.get('typologie', ''),
                        criticite=row.get('criticite', ''),
                        remonter_tdb=row.get('remonter_tdb', 'False').lower() == 'true',
                        solution_proposee=row.get('solution_proposee', ''),
                        porteur_solution=row.get('porteur_solution', ''),
                        delai_mise_en_oeuvre=parse_date(row.get('delai_mise_en_oeuvre', '')),
                        statut_solution=row.get('statut_solution', '')
                    )
                    success_count += 1
                    
                except Exception as e:
                    errors.append(f"Ligne {row_num}: {str(e)}")
            
            if success_count > 0:
                messages.success(request, f"{success_count} problèmes importés avec succès!")
            if errors:
                messages.error(request, f"Erreurs sur {len(errors)} lignes. {' | '.join(errors[:3])}" + ("..." if len(errors)>3 else ""))
            
            #return redirect('tables/problemes/import-csv/')
    else:
        form = UploadCSVForm()
    
    return render(request, 'tables/import_problem.html', {'form': form})


## viewer
@login_required(login_url=reverse_lazy('sing_in'))
def ajouter_probleme(request):
    ajoutproblemeform=ProblemeForm()
    if request.method=='POST':
        ajoutproblemeform=ProblemeForm(request.POST)
        if ajoutproblemeform.is_valid():
            ajoutproblemeform.save()
            return redirect('/tables/problemes')
    context={'form': ajoutproblemeform}
    return render(request, 'tables/Ajout_probleme.html', context)

## viewer
@login_required(login_url=reverse_lazy('sing_in'))
def modifie_probleme(request, rk):
    probleme=Probleme.objects.get(id=rk)
    modifieproblemeform=ProblemeForm(instance=probleme)
    if request.method=='POST':
        modifieproblemeform=ProblemeForm(request.POST, instance=probleme)
        if modifieproblemeform.is_valid():
            modifieproblemeform.save()
            return redirect('/tables/problemes')
    context={'form': modifieproblemeform}
    return render(request, 'tables/Ajout_probleme.html', context)

def supprimer_probleme(request, pk):
    probleme = get_object_or_404(Probleme, pk=pk)
    probleme.delete()
    messages.success(request, "Le problème a été supprimé avec succès.")
    return redirect('tables_sub4')

## viewer
@login_required(login_url=reverse_lazy('sing_in'))
def ajouter_composante(request):
    ajoutcomposanteform=ComposanteForm()
    if request.method=='POST':
        ajoutcomposanteform=ComposanteForm(request.POST)
        if ajoutcomposanteform.is_valid():
            ajoutcomposanteform.save()
            return redirect('/tables/composantes')
    context={'form': ajoutcomposanteform}
    return render(request, 'tables/Ajout_composante.html', context)

## viewer
@login_required(login_url=reverse_lazy('sing_in'))
def modifie_composante(request, rk):
    composante=Composante.objects.get(id=rk)
    modifiecomposanteform=ComposanteForm(instance=composante)
    if request.method=='POST':
        modifiecomposanteform=ComposanteForm(request.POST, instance=composante)
        if modifiecomposanteform.is_valid():
            modifiecomposanteform.save()
            return redirect('/tables/composantes')
    context={'form': modifiecomposanteform}
    return render(request, 'tables/Ajout_composante.html', context)

def supprimer_composante(request, pk):
    composante = get_object_or_404(Composante, pk=pk)
    composante.delete()
    messages.success(request, "La composante a été supprimée avec succès.")
    return redirect('tables_sub2')
## viewer
@login_required(login_url=reverse_lazy('sing_in'))
def ajouter_message(request):
    ajoutmessageform=MessageForm()
    if request.method=='POST':
        ajoutmessageform=MessageForm(request.POST)
        if ajoutmessageform.is_valid():
            ajoutmessageform.save()
            return redirect('/tables/messages')
    context={'form': ajoutmessageform}
    return render(request, 'tables/Ajout_message.html', context)


## viewer
@login_required(login_url=reverse_lazy('sing_in'))
def import_csv_message(request):
    if request.method == 'POST':
        form = UploadCSVForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = TextIOWrapper(request.FILES['csv_file'].file, encoding='utf-8')
            reader = csv.DictReader(csv_file)

            success_count = 0
            errors = []

            for row_num, row in enumerate(reader, start=2):
                try:
                    # Portefeuille
                    portefeuille_nom = row.get('portefeuille', '').strip()
                    if not portefeuille_nom:
                        raise ValidationError("Le portefeuille est requis")
                    try:
                        portefeuille = Portefeuille.objects.get(nom=portefeuille_nom)
                    except ObjectDoesNotExist:
                        raise ValidationError(f"Le portefeuille '{portefeuille_nom}' n'existe pas")

                    # Composante
                    composante_nom = row.get('composante', '').strip()
                    if not composante_nom:
                        raise ValidationError("La composante est requise")
                    try:
                        composante = Composante.objects.get(nom=composante_nom)
                    except ObjectDoesNotExist:
                        raise ValidationError(f"La composante '{composante_nom}' n'existe pas")

                    # Parsing de la date de création (avec heure par défaut si absente)
                    def parse_date_with_default(date_str, default=datetime.min):
                        formats = [
                                "%Y-%m-%d",  # Format ISO (standard)
                                "%d/%m/%Y",  # Format français
                                "%m/%d/%Y",  # Format américain (ton cas)
                                "%d-%m-%Y",  # Variante
                                "%m-%d-%Y", 
                            ]  # ajoute les formats nécessaires
                        for fmt in formats:
                            try:
                                return datetime.strptime(date_str, fmt)
                            except ValueError:
                                continue
                        return default

                    date_creation_str = row.get('date_creation', '').strip()
                    date_creation = None
                    if date_creation_str:
                        date_creation = parse_date_with_default(date_creation_str)
                        
                    # Problème (facultatif)
                    probleme_titre = row.get('probleme', '').strip()
                    if probleme_titre:
                        try:
                            probleme = Probleme.objects.get(titre=probleme_titre)
                        except ObjectDoesNotExist:
                            raise ValidationError(f"Le problème '{probleme_titre}' n'existe pas")

                    # Création du message
                    Message.objects.create(
                        portefeuille=portefeuille,
                        composante=composante,
                        probleme=probleme,
                        contenu=row.get('contenu', '').strip(),
                        remonter_message_tdb=row.get('remonter_message_tdb', 'False').strip().lower() == 'true',
                        date_creation=date_creation
                    )
                    success_count += 1

                except Exception as e:
                    errors.append(f"Ligne {row_num}: {str(e)}")

            if success_count > 0:
                messages.success(request, f"{success_count} messages importés avec succès !")
            if errors:
                messages.error(request, f"Erreurs sur {len(errors)} lignes. {' | '.join(errors[:3])}" + ("..." if len(errors) > 3 else ""))

    else:
        form = UploadCSVForm()

    return render(request, 'tables/import_message.html', {'form': form})

## viewer
@login_required(login_url=reverse_lazy('sing_in'))
def modifie_message(request, rk):
    message=Message.objects.get(id=rk)
    modifiemessageform=MessageForm(instance=message)
    if request.method=='POST':
        modifiemessageform=MessageForm(request.POST, instance=message)
        if modifiemessageform.is_valid():
            modifiemessageform.save()
            return redirect('/tables/messages')
    context={'form': modifiemessageform}
    return render(request, 'tables/Ajout_message.html', context)


def supprimer_message(request, pk):
    message = get_object_or_404(Message, pk=pk)
    message.delete()
    messages.success(request, "Le message a été supprimé avec succès.")
    return redirect('tables_sub5')

## Vues pour le dashbooard_Coordoo

from django.http import JsonResponse
from django.core import serializers

def get_filter_options(request):
    filter_type = request.GET.get('filter_type')
    
    if filter_type == 'Axe':
        data = list(Axe.objects.values('id', 'nom'))
    elif filter_type == 'Portefeuille':
        data = list(Portefeuille.objects.values('id', 'nom'))
    elif filter_type == 'Ministere_responsable':
        data = list(Projet.objects.values('ministere_responsable').distinct())
    else:
        data = []
    
    return JsonResponse(data, safe=False)

def get_stats(request):
    filter_type = request.GET.get('filter_type')
    filter_value = request.GET.get('filter_value')
    
    stats = {}
    
    if filter_type == 'Axe':
        stats = {
            'nb_projets': Projet.objects.filter(programme__axe__nom=filter_value).count(),
            'nb_projets_demarres': Projet.objects.filter(programme__axe__nom=filter_value, est_lance=True).count(),
            'nb_programmes': Programme.objects.filter(axe__nom=filter_value).count(),
            'responsables': list(Portefeuille.objects.filter(axe__nom=filter_value).values('responsable').distinct())
        }
    elif filter_type == 'Portefeuille':
        stats = {
            'nb_projets': Projet.objects.filter(programme__portefeuille__nom=filter_value).count(),
            'nb_projets_demarres': Projet.objects.filter(programme__portefeuille__nom=filter_value, est_lance=True).count(),
            'nb_programmes': Programme.objects.filter(portefeuille__nom=filter_value).count(),
            'responsables': [{'responsable': Portefeuille.objects.get(nom=filter_value).responsable}]
        }
    elif filter_type == 'Ministere_responsable':
        stats = {
            'nb_projets': Projet.objects.filter(ministere_responsable=filter_value).count(),
            'nb_projets_demarres': Projet.objects.filter(ministere_responsable=filter_value, est_lance=True).count(),
            'nb_programmes': Programme.objects.filter(projet__ministere_responsable=filter_value).distinct().count(),
            'responsables': list(Portefeuille.objects.filter(programme__projet__ministere_responsable=filter_value).values('responsable').distinct())
        }
    else:  # Tous
        stats = {
            'nb_projets': Projet.objects.count(),
            'nb_projets_demarres': Projet.objects.filter(est_lance=True).count(),
            'nb_programmes': Programme.objects.count(),
            'responsables': list(Portefeuille.objects.values('responsable').distinct())
        }
    
    return JsonResponse(stats)

## viewer
@login_required(login_url=reverse_lazy('sing_in'))
def dashboard_coordo(request):

    # Récupérer les données pour les filtres
    axes = Axe.objects.all()
    portefeuilles = Portefeuille.objects.all()
    ministeres = Projet.objects.values_list('ministere_responsable', flat=True).distinct()
    
    # Initialisation des variables
    stats = None
    l2_options = []
    l1_choice = request.GET.get('l1_filter', 'Tous')
    l2_choice = request.GET.get('l2_filter')
    
    # Déterminer les options pour L2 en fonction de L1
    if l1_choice == 'Axe':
        l2_options = Axe.objects.all()
    elif l1_choice == 'Portefeuille':
        l2_options = Portefeuille.objects.all()
    elif l1_choice == 'Ministere_responsable':
        l2_options = Projet.objects.values_list('ministere_responsable', flat=True).distinct()
    
    # Calculer les statistiques en fonction des filtres
    if l2_choice:
        if l1_choice == 'Axe':
            stats = {
                'nb_projets': Projet.objects.filter(programme__axe__nom=l2_choice).count(),
                'nb_projets_demarres': Projet.objects.filter(programme__axe__nom=l2_choice, est_lance=True).count(),
                'nb_programmes': Programme.objects.filter(axe__nom=l2_choice).count(),
                'responsables': Portefeuille.objects.filter(axe__nom=l2_choice).values('responsable').distinct()
            }
        elif l1_choice == 'Portefeuille':
            stats = {
                'nb_projets': Projet.objects.filter(programme__portefeuille__nom=l2_choice).count(),
                'nb_projets_demarres': Projet.objects.filter(programme__portefeuille__nom=l2_choice, est_lance=True).count(),
                'nb_programmes': Programme.objects.filter(portefeuille__nom=l2_choice).count(),
                'responsable': Portefeuille.objects.get(nom=l2_choice).responsable
            }
        elif l1_choice == 'Ministere_responsable':
            stats = {
                'nb_projets': Projet.objects.filter(ministere_responsable=l2_choice).count(),
                'nb_projets_demarres': Projet.objects.filter(ministere_responsable=l2_choice, est_lance=True).count(),
                'nb_programmes': Programme.objects.filter(projet__ministere_responsable=l2_choice).distinct().count(),
                'responsables': Portefeuille.objects.filter(programme__projet__ministere_responsable=l2_choice).values('responsable').distinct()
            }
        else:  # Tous
            stats = {
                'nb_projets': Projet.objects.count(),
                'nb_projets_demarres': Projet.objects.filter(est_lance=True).count(),
                'nb_programmes': Programme.objects.count(),
                'responsables': Portefeuille.objects.values('responsable').distinct()
            }
    
    context = {
        'axes': axes,
        'portefeuilles': portefeuilles,
        'ministeres': ministeres,
        'l1_choice': l1_choice,
        'l2_options': l2_options,
        'l2_choice': l2_choice,
        'stats': stats,
        'initial_l1_filter': request.GET.get('l1_filter', 'Tous'),
        'initial_l2_filter': request.GET.get('l2_filter', ''),
    }
    return render(request, 'dashboard_app/dashboard_cordo2.html', context)



###############"""
# 
from django.http import JsonResponse
from django.db.models import Count, Q
from .models import Axe, Portefeuille, Programme, Projet, Composante, Message

def l2_filter_options(request):
    l1_value = request.GET.get('l1')
    options = []
    
    if l1_value == 'axe':
        options = [{'id': axe.id, 'name': axe.nom} for axe in Axe.objects.all()]
    elif l1_value == 'portefeuille':
        options = [{'id': pf.id, 'name': pf.nom} for pf in Portefeuille.objects.all()]
    elif l1_value == 'ministere':
        # Récupère les ministères uniques
        options = [{'id': min, 'name': min} for min in Projet.objects.values_list('ministere_responsable', flat=True).distinct()]
    
    return JsonResponse({'options': options})

def l3_filter_options(request):
    l1_value = request.GET.get('l1')
    l2_value = request.GET.get('l2')
    
    if l1_value == 'axe':
        programmes = Programme.objects.filter(axe_id=l2_value)
    elif l1_value == 'portefeuille':
        programmes = Programme.objects.filter(portefeuille_id=l2_value)
    elif l1_value == 'ministere':
        projets = Projet.objects.filter(ministere_responsable=l2_value)
        programme_ids = projets.values_list('programme_id', flat=True).distinct()
        programmes = Programme.objects.filter(id__in=programme_ids)
    
    options = [{'id': prog.id, 'name': prog.nom} for prog in programmes]
    return JsonResponse({'options': options})

def l4_filter_options(request):
    programme_id = request.GET.get('l3')
    projets = Projet.objects.filter(programme_id=programme_id)
    options = [{'id': p.id, 'name': p.nom} for p in projets]
    return JsonResponse({'options': options})

def l5_filter_options(request):
    projet_id = request.GET.get('l4')
    composantes = Composante.objects.filter(projet_id=projet_id)
    options = [{'id': c.id, 'name': c.nom} for c in composantes]
    return JsonResponse({'options': options})

def get_stats(request):
    l1_value = request.GET.get('l1')
    l2_value = request.GET.get('l2')
    
    stats = {}
    
    if l1_value == 'axe':
        axe = Axe.objects.get(id=l2_value)
        stats['program_count'] = Programme.objects.filter(axe=axe).count()
        stats['project_count'] = Projet.objects.filter(programme__axe=axe).count()
        stats['started_project_count'] = Projet.objects.filter(programme__axe=axe, est_lance=True).count()
        stats['started_composante_count'] = Composante.objects.filter(projet__programme__axe=axe, statut='En cours').count()
        stats['satisfaisant_composante_count'] = Composante.objects.filter(projet__programme__axe=axe, etat='En cours').count()
        stats['alerte_composante_count'] = Composante.objects.filter(projet__programme__axe=axe,
            etat__in=['En cours avec difficulté mineure', 'En cours avec difficulté majeure']).count()
        stats['bloque_composante_count'] = Composante.objects.filter(projet__programme__axe=axe, etat='Bloquée').count()
    elif l1_value == 'portefeuille':
        portefeuille = Portefeuille.objects.get(id=l2_value)
        stats['responsable'] = portefeuille.responsable
        stats['program_count'] = Programme.objects.filter(portefeuille=portefeuille).count()
        stats['project_count'] = Projet.objects.filter(programme__portefeuille=portefeuille).count()
        stats['started_project_count'] = Projet.objects.filter(programme__portefeuille=portefeuille, est_lance=True).count()
        # Ajout du comptage des composantes lancées
        stats['started_composante_count'] = Composante.objects.filter(projet__programme__portefeuille=portefeuille, statut='En cours').count()
        stats['satisfaisant_composante_count'] = Composante.objects.filter(projet__programme__portefeuille=portefeuille, etat='En cours').count()
        stats['alerte_composante_count'] = Composante.objects.filter(projet__programme__portefeuille=portefeuille,
            etat__in=['En cours avec difficulté mineure', 'En cours avec difficulté majeure']).count()
        stats['bloque_composante_count'] = Composante.objects.filter(projet__programme__portefeuille=portefeuille, etat='Bloquée').count()

    elif l1_value == 'ministere':
        stats['program_count'] = Programme.objects.filter(
            projet__ministere_responsable=l2_value
        ).distinct().count()
        stats['project_count'] = Projet.objects.filter(ministere_responsable=l2_value).count()
        stats['started_project_count'] = Projet.objects.filter(ministere_responsable=l2_value, est_lance=True).count()
        # Ajout du comptage des composantes lancées
        stats['started_composante_count'] = Composante.objects.filter(projet__ministere_responsable=l2_value, statut='En cours').count()
        stats['satisfaisant_composante_count'] = Composante.objects.filter(projet__ministere_responsable=l2_value, etat='En cours').count()
        stats['alerte_composante_count'] = Composante.objects.filter(projet__ministere_responsable=l2_value,
            etat__in=['En cours avec difficulté mineure', 'En cours avec difficulté majeure']).count()
        stats['bloque_composante_count'] = Composante.objects.filter(projet__ministere_responsable=l2_value, etat='Bloquée').count()
    
    return JsonResponse(stats)

def global_stats(request):
    stats = {
        'axe_count': Axe.objects.count(),
        'portefeuille_count': Portefeuille.objects.count(),
        'program_count': Programme.objects.count(),
        'project_count': Projet.objects.count(),
        'started_composante_count': Composante.objects.filter(statut='En cours').count(),
        'satisfaisant_composante_count': Composante.objects.filter(etat='En cours').count(),
        'alerte_composante_count': Composante.objects.filter(etat__in=['En cours avec difficulté mineure', 'En cours avec difficulté majeure']).count(),
        'bloque_composante_count': Composante.objects.filter(etat='Bloquée').count()
    }
    return JsonResponse(stats)

def composante_details(request, composante_id):
    composante = Composante.objects.get(id=composante_id)
    data = {
        'nom': composante.nom,
        'localisation': composante.localisation,
        'tutelle': composante.tutelle,
        'statut': composante.statut,
        'cible_fin_annee_finc': float(composante.cible_total) if composante.cible_total else 0,
        'cible_fin_annee_dec': float(composante.dec_cible) if composante.dec_cible else 0,
        'taux_decaissement': float(composante.taux_decaissement) if composante.taux_decaissement else 0,
        'taux_decaissement': float(composante.taux_decaissement) if composante.taux_decaissement else 0,
        'dec_reel_t1': float(composante.dec_reel_t1) if composante.dec_reel_t1 else 0,
        'dec_reel_t2': float(composante.dec_reel_t2) if composante.dec_reel_t2 else 0,
        'dec_reel_t3': float(composante.dec_reel_t3) if composante.dec_reel_t3 else 0,
        'dec_reel_t4': float(composante.dec_reel_t4) if composante.dec_reel_t4 else 0,
        'dec_prev_t1': float(composante.dec_prev_t1) if composante.dec_prev_t1 else 0,
        'dec_prev_t2': float(composante.dec_prev_t2) if composante.dec_prev_t2 else 0,
        'dec_prev_t3': float(composante.dec_prev_t3) if composante.dec_prev_t3 else 0,
        'dec_prev_t4': float(composante.dec_prev_t4) if composante.dec_prev_t4 else 0,
        'realise_t1_total': float(composante.realise_t1_total) if composante.realise_t1_total else 0,
        'realise_t2_total': float(composante.realise_t2_total) if composante.realise_t2_total else 0,
        'realise_t3_total': float(composante.realise_t3_total) if composante.realise_t3_total else 0,
        'realise_t4_total': float(composante.realise_t4_total) if composante.realise_t4_total else 0,
        'prev_t1_total': float(composante.prev_t1_total) if composante.prev_t1_total else 0,
        'prev_t2_total': float(composante.prev_t2_total) if composante.prev_t2_total else 0,
        'prev_t3_total': float(composante.prev_t3_total) if composante.prev_t3_total else 0,
        'prev_t4_total': float(composante.prev_t4_total) if composante.prev_t4_total else 0,
    }
    return JsonResponse(data)

def get_messages(request):
    composante_id = request.GET.get('composante')
    messages = Message.objects.filter(composante_id=composante_id).order_by('-date_creation')
    
    data = []
    for msg in messages:
        data.append({
            'probleme': msg.probleme.titre if msg.probleme else None,
            'contenu': msg.contenu,
            'date_creation': msg.date_creation.strftime('%d/%m/%Y %H:%M'),
            'remonter_message_tdb': msg.remonter_message_tdb,
        })
    
    return JsonResponse(data, safe=False)


def get_problemes(request):
    composante_id = request.GET.get('composante')
    problemes = Probleme.objects.filter(composante_id=composante_id)
    
    data = []
    for pb in problemes:
        data.append({
            'titre': pb.titre if pb.titre else None,
            'description': pb.description,
            'date_identification': pb.date_identification.strftime('%d/%m/%Y %H:%M'),
            'typologie': pb.typologie,
            'source': pb.source,
            'criticite': pb.criticite,
            'remonter_tdb': pb.remonter_tdb,
            'solution_proposee': pb.solution_proposee,
            'porteur_solution': pb.porteur_solution,
            'delai_mise_en_oeuvre': pb.delai_mise_en_oeuvre,
            'statut_solution': pb.statut_solution,
            'nombre_de_jours_retard': pb.nombre_de_jours_retard,

        })
    
    return JsonResponse(data, safe=False)




## partie pour les composantes performantes ou non


def data_get_view_Coord(request):
    Axes= Axe.objects.all()
    Portefeuilles= Portefeuille.objects.all()
    Programmes= Programme.objects.all()
    Projets= Projet.objects.all()
    Composantes= Composante.objects.all()
    Activites= Activite.objects.all()
    Problemes= Probleme.objects.all()
    Messages_week=Message.objects.order_by('-date_creation')[:1]  # Uniquement le plus récent
    ministeres = Projet.objects.values_list('ministere_responsable', flat=True).distinct()


    # Sérialiser les données en incluant les propriétés calculées pour les composantes
    composantes_data = []
    for composante in Composantes:
        composante_dict = {
            'id': composante.id,
            'projet_id': composante.projet_id,
            'nom': composante.nom,
            'identifiant': composante.identifiant,
            'localisation': composante.localisation,
            'tutelle': composante.tutelle,
            'agence_execution': composante.agence_execution,
            'date_lancement': composante.date_lancement.strftime('%Y-%m-%d') if composante.date_lancement else None,
            'duree_mois': composante.duree_mois,
            'cout': float(composante.cout) if composante.cout else None,
            'statut': composante.statut,
            'partenaire_pad': composante.partenaire_pad,
            'facteurs_explication': composante.facteurs_explication,
            'etat':composante.etat,
            # Décaissement
            'dec_prev_t1': float(composante.dec_prev_t1) if composante.dec_prev_t1 else None,
            'dec_prev_t2': float(composante.dec_prev_t2) if composante.dec_prev_t2 else None,
            'dec_prev_t3': float(composante.dec_prev_t3) if composante.dec_prev_t3 else None,
            'dec_prev_t4': float(composante.dec_prev_t4) if composante.dec_prev_t4 else None,
            'dec_cible': float(composante.dec_cible) if composante.dec_cible else None,
            'dec_reel_t1': float(composante.dec_reel_t1) if composante.dec_reel_t1 else None,
            'dec_reel_t2': float(composante.dec_reel_t2) if composante.dec_reel_t2 else None,
            'dec_reel_t3': float(composante.dec_reel_t3) if composante.dec_reel_t3 else None,
            'dec_reel_t4': float(composante.dec_reel_t4) if composante.dec_reel_t4 else None,
            'taux_decaissement': float(composante.taux_decaissement) if composante.taux_decaissement else None,
            
            # Ajouter les propriétés calculées ici
            'prev_t1_total': float(composante.prev_t1_total) if composante.prev_t1_total is not None else None,
            'prev_t2_total': float(composante.prev_t2_total) if composante.prev_t2_total is not None else None,
            'prev_t3_total': float(composante.prev_t3_total) if composante.prev_t3_total is not None else None,
            'prev_t4_total': float(composante.prev_t4_total) if composante.prev_t4_total is not None else None,
            'cible_total': float(composante.cible_total) if composante.cible_total is not None else None,
            'realise_t1_total': float(composante.realise_t1_total) if composante.realise_t1_total is not None else None,
            'realise_t2_total': float(composante.realise_t2_total) if composante.realise_t2_total is not None else None,
            'realise_t3_total': float(composante.realise_t3_total) if composante.realise_t3_total is not None else None,
            'realise_t4_total': float(composante.realise_t4_total) if composante.realise_t4_total is not None else None,
            'avancement_physique_total': float(composante.avancement_physique_total) if composante.avancement_physique_total is not None else None,
        }
        composantes_data.append(composante_dict)

    return  JsonResponse({
        'Axes': list(Axes.values()),
        'Portefeuilles': list(Portefeuilles.values()),
        'Programmes': list(Programmes.values()),
        'Projets': list(Projets.values()),
        'Composantes': composantes_data,
        'Activites': list(Activites.values()),
        'Problemes': list(Problemes.values()),
        'ministeres': list(ministeres.values()),
        'Messages_week' : list(Messages_week.values())
    })



