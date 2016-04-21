from django.forms import ModelForm
from .models import Source

class SourceForm(ModelForm):
    class Meta:
        model = Source
        fields = ('url', 'sourcetype', 'default_author', 'name')
