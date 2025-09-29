from django import forms

class CompetitionForm(forms.Form):
    od_from      = forms.CharField(max_length=3)
    od_to        = forms.CharField(max_length=3)
    finnair      = forms.BooleanField()
    aeroflot     = forms.BooleanField()
    rossiya      = forms.BooleanField()
    airbaltic    = forms.BooleanField()
    dep_from     = forms.DateField()
    dep_to       = forms.DateField()
    monday       = forms.BooleanField()
    tuesday      = forms.BooleanField()
    wednesday    = forms.BooleanField()
    thursday     = forms.BooleanField()
    friday       = forms.BooleanField()
    saturday     = forms.BooleanField()
    sunday       = forms.BooleanField()
    sl_days      = forms.CharField()

    def is_valid(self):
        return True
