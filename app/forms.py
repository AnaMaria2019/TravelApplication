from django import forms
import datetime


class SearchForm(forms.Form):
    from_location = forms.CharField(label='From Airport', max_length=150)
    to_location = forms.CharField(label='To Airport', max_length=150)
    start_date = forms.DateField(initial=datetime.date.today, input_formats=['%Y-%m-%d'])
    end_date = forms.DateField(initial=datetime.date.today, input_formats=['%Y-%m-%d'])
    budget = forms.IntegerField(label='Buget alocat')
    nr_persons = forms.IntegerField(label='Numar persoane')
    nr_rooms = forms.IntegerField(label='Numar camere')
