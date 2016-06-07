from django.forms import ModelForm, HiddenInput
from .models import *

class SourceForm(ModelForm):
    class Meta:
        model = Source
        fields = ('url', 'sourcetype', 'default_author', 'name')

class DocEditForm(ModelForm):
    class Meta:
        model = Doc
        fields = ('doc_id', 'authors', 'title', 'abstract', 'hidden')
        #widgets = {'doc_id': HiddenInput()}
