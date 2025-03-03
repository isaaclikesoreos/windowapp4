from django import forms
from .models import JobEntry

class JobEntryForm(forms.ModelForm):
    is_repairable = forms.TypedChoiceField(
        choices=((True, "Yes"), (False, "No")),
        coerce=lambda x: x == 'True',
        widget=forms.RadioSelect,
        required=False,
        label="Is it repairable?"
    )

    class Meta:
        model = JobEntry
        fields = [
            'damage_piece', 'damage_side', 'cause_of_damage', 'impacting_driving', 'is_repairable',
            'first_name', 'last_name', 'phone', 'email', 'vin',
            'has_insurance_claim', 'insurance_name', 'policy_number', 'claim_number', 'referral_number',
            'has_extended_warranty'
        ]
        widgets = {
            'impacting_driving': forms.CheckboxInput(),
            'has_insurance_claim': forms.RadioSelect(choices=[(True, 'Yes'), (False, 'No')]),
            'has_extended_warranty': forms.RadioSelect(choices=[(True, 'Yes'), (False, 'No')]),
            'first_name': forms.TextInput(attrs={'size': '10', 'style': 'max-width: 10ch;'}),
            'last_name': forms.TextInput(attrs={'size': '10', 'style': 'max-width: 10ch;'}),
            'phone': forms.TextInput(attrs={'size': '10', 'style': 'max-width: 10ch;'}),
            'email': forms.EmailInput(attrs={'size': '20', 'style': 'max-width: 20ch;'}),
            'vin': forms.TextInput(attrs={'size': '18', 'style': 'max-width: 18ch;'}),
            'damage_side': forms.RadioSelect(choices=[('driver', "Driver"), ('passenger', "Passenger")]),
            'is_repairable': forms.RadioSelect(choices=[(True, "Yes"), (False, "No")]),
            'insurance_name': forms.TextInput(attrs={'size': '25', 'style': 'max-width: 25ch;'}),
            'policy_number': forms.TextInput(attrs={'size': '25', 'style': 'max-width: 25ch;'}),
            'claim_number': forms.TextInput(attrs={'size': '25', 'style': 'max-width: 25ch;'}),
            'referral_number': forms.TextInput(attrs={'size': '25', 'style': 'max-width: 25ch;'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove empty choice for damage_side
        self.fields['damage_side'].choices = [
            choice for choice in self.fields['damage_side'].choices if choice[0] != ''
        ]
