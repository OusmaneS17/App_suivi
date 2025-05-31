from django.forms import ModelForm
from .models import Projet, Activite, Probleme, Composante
from django import forms

from django import forms
from .models import Probleme

class UploadCSVForm(forms.Form):
    csv_file = forms.FileField(label='Fichier CSV')

    
class ProjetForm(ModelForm):
    class Meta:
        model = Projet
        fields = '__all__'
        
        

class ActiviteForm(ModelForm):
    class Meta:
        model = Activite
        fields = '__all__'


class ProblemeForm(ModelForm):
    class Meta:
        model = Probleme
        fields = '__all__'


class ComposanteForm(ModelForm):
    class Meta:
        model = Composante
        fields = '__all__'
        