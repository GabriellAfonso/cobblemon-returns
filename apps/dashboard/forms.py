from django import forms

from apps.wiki.models import WikiPage


class WikiPageForm(forms.ModelForm):
    class Meta:
        model = WikiPage
        fields = ['title', 'slug', 'content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 20, 'class': 'wiki-content-input'}),
            'title': forms.TextInput(attrs={'class': 'form-input'}),
            'slug': forms.TextInput(attrs={'class': 'form-input'}),
        }
