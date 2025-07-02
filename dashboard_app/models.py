from django.db import models
from django.db.models import Sum, FloatField, ExpressionWrapper
from django.db.models import F, Sum, ExpressionWrapper, FloatField
from simple_history.models import HistoricalRecords
from simple_history import register
from django.contrib.auth.models import User
# Create your models here.
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('lamda', 'lamda'),
        ('coordonateur', 'Coordonateur'),
        ('gestionnaire', 'Gestionnaire de portefeuille'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='lamda')
    nom = models.CharField(max_length=150, blank=True)



class Axe(models.Model):
    nom = models.CharField(max_length=255)

    def __str__(self):
        return self.nom

class Portefeuille(models.Model):
    nom = models.CharField(max_length=255)
    responsable = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'gestionnaire'})
    axe = models.ForeignKey(Axe, on_delete=models.CASCADE, default=None)
    history_portefeuille = HistoricalRecords()

    def __str__(self):
        return self.nom

class Programme(models.Model):
    axe = models.ForeignKey(Axe, on_delete=models.CASCADE)
    portefeuille = models.ForeignKey(Portefeuille, on_delete=models.SET_NULL, null=True)
    nom = models.CharField(max_length=255)
    identifiant = models.CharField(max_length=100)
    history_program = HistoricalRecords()

    def __str__(self):
        return self.nom

class Projet(models.Model):
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE)
    identifiant = models.CharField(max_length=100)
    nom = models.CharField(max_length=255)
    est_lance = models.BooleanField(default=False)
    ministere_responsable = models.CharField(max_length=255)
    chef_projet = models.CharField(max_length=255)
    email = models.EmailField()
    tel = models.CharField(max_length=20)
    history = HistoricalRecords() # new line

    def __str__(self):
        return self.nom

class Composante(models.Model):
    projet = models.ForeignKey(Projet, on_delete=models.CASCADE)
    identifiant = models.CharField(max_length=100)
    nom = models.CharField(max_length=255)
    localisation = models.CharField(max_length=255)
    tutelle = models.CharField(max_length=255)
    agence_execution = models.CharField(max_length=255)
    date_lancement = models.DateField(null=True, blank=True)
    duree_mois = models.IntegerField(null=True, blank=True)
    cout = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    Fin_previsionnelle = models.DateField(null=True, blank=True)
    
    financement_public = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    financement_prive = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    financement_ppp = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    partenaire_pad = models.TextField(blank=True, null=True)
    statut = models.CharField(
        max_length=50,
        choices=[
            ('En cours', 'En cours'),
            ('Bloquée', 'Bloquée'),
            ('Terminée', 'Terminée'),
            ('Dépriorisée', 'Dépriorisée')
        ]
    )

    
    etat = models.CharField(
        max_length=50,null=True,
        choices=[
            ('En cours', 'En cours'),
            ('En cours avec difficulté mineure', 'En cours avec difficulté mineure'),
            ('En cours avec difficulté majeure', 'En cours avec difficulté majeure'),
            ('Bloquée', 'Bloquée')
        ])
    
    def total_pourcentage_financement(self):
        return sum([
            self.financement_public or 0,
            self.financement_prive or 0,
            self.financement_ppp or 0
        ])

    def clean(self):
        from django.core.exceptions import ValidationError
        total = self.total_pourcentage_financement()
        if total != 100:
            raise ValidationError("La somme des pourcentages de financement (public, privé, PPP) doit être exactement égale à 100 %. Actuellement : %.2f%%")
        

   

    @property
    def pondération_totale(self):
        return self.activite_set.aggregate(
            total=Sum('ponderation')
        )['total'] or 0

    def somme_pondérée(self, champ):
        return self.activite_set.aggregate(
            total=Sum(
                ExpressionWrapper(
                    F('ponderation') * F(champ),
                    output_field=FloatField()
                )
            )
        )['total'] or 0
    
    facteurs_explication = models.TextField(null=True, blank=True)

    
    # Décaissement
    dec_prev_t1 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    dec_prev_t2 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    dec_prev_t3 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    dec_prev_t4 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    dec_cible = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    dec_reel_t1 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    dec_reel_t2 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    dec_reel_t3 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    dec_reel_t4 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    taux_decaissement = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)


    @property
    def prev_t1_total(self):
        return self.somme_pondérée('prev_t1')/ 100

    @property
    def prev_t2_total(self):
        return self.somme_pondérée('prev_t2')/ 100

    @property
    def prev_t3_total(self):
        return self.somme_pondérée('prev_t3')/ 100

    @property
    def prev_t4_total(self):
        return self.somme_pondérée('prev_t4')/ 100

    @property
    def cible_total(self):
        return self.somme_pondérée('cible_fin_annee')/ 100

    @property
    def realise_t1_total(self):
        return self.somme_pondérée('realise_t1')/ 100

    @property
    def realise_t2_total(self):
        return self.somme_pondérée('realise_t2')/ 100

    @property
    def realise_t3_total(self):
        return self.somme_pondérée('realise_t3')/ 100

    @property
    def realise_t4_total(self):
        return self.somme_pondérée('realise_t4')/ 100

    @property
    def avancement_physique_total(self):
        return self.somme_pondérée('avancement_physique')/ 100
    
    history = HistoricalRecords()
    
    
    def __str__(self):
        return self.nom

class Activite(models.Model):
    composante = models.ForeignKey(Composante, on_delete=models.CASCADE)
    identifiant = models.CharField(max_length=100)
    nom = models.CharField(max_length=255)
    ponderation = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # Avancement physique
    prev_t1 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    prev_t2 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    prev_t3 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    prev_t4 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    cible_fin_annee = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    realise_t1 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    realise_t2 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    realise_t3 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    realise_t4 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    avancement_physique = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.nom

class Probleme(models.Model):
    composante = models.ForeignKey(Composante, on_delete=models.CASCADE)
    identifiant = models.CharField(max_length=100)
    titre = models.CharField(max_length=255)
    description = models.TextField()
    date_identification = models.DateField(null=True, blank=True)
    delai_mise_en_oeuvre = models.DateField(null=True, blank=True)

    @property
    def nombre_de_jours_retard(self):
        if self.date_identification and self.delai_mise_en_oeuvre:
            return (self.delai_mise_en_oeuvre - self.date_identification).days
        return None
    
    source = models.CharField(max_length=255)
    typologie = models.CharField(max_length=255, choices=[
            ('Financière', 'Financière'),
            ('Administratif', 'Administratif'),
            ('Contractuel', 'Contractuel'),
            ('Foncier', 'Foncier'),
            ('Opérationnel', 'Opérationnel'),
            ('Règlementaire', 'Règlementaire'),
        ])
    criticite = models.CharField(max_length=255, choices=[
            ('Moyenne', 'Moyenne'),
            ('Elevée', 'Elevée'),
            ('Faible', 'Faible'),
        ])
    remonter_tdb = models.BooleanField(default=False)
    solution_proposee = models.TextField()
    porteur_solution = models.CharField(max_length=255)
    statut_solution = models.CharField(max_length=255, choices=[
            ('Cloturé', 'Cloturé'),
            ('En cours', 'En cours'),
            ('Ouvert', 'Ouvert'),
        ])
    history = HistoricalRecords()

    def __str__(self):
        return self.titre
    

class Message(models.Model):
    portefeuille = models.ForeignKey( Portefeuille, on_delete=models.CASCADE, verbose_name="Portefeuille associé" )
    composante = models.ForeignKey(Composante, on_delete=models.CASCADE, verbose_name="Composante concernée")
    probleme = models.ForeignKey(Probleme, on_delete=models.CASCADE,verbose_name="Problème lié", null=True, blank=True)
    contenu = models.TextField(verbose_name="Contenu du message")
    date_creation = models.DateTimeField(verbose_name="Date de création", auto_now_add=True)
    remonter_message_tdb = models.BooleanField(default=False, verbose_name="Remonter au tableau de bord")
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Message"
        verbose_name_plural = "Messages"
        ordering = ['-date_creation']  # Plus récents en premier

    def __str__(self):
        return f"Message du {self.date_creation.strftime('%d/%m/%Y')} - {self.contenu[:50]}..."




