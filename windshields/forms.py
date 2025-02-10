from django import forms
from .models import JobEntry


class JobEntryForm(forms.ModelForm):

    door_side = forms.ChoiceField(
        choices=[('driver', "Driver's Side"), ('passenger', "Passenger's Side")],
        required=False  # Only required if a door glass is selected
    )

    class Meta:
        model = JobEntry
        fields = [
            # Step 1 – Damage Information
            'damage_piece', 'damage_side', 'cause_of_damage', 'impacting_driving',
            # Step 2 – Repair Option (if applicable)
            'is_quarter_damage',
            # Step 3 – Customer Information
            'first_name', 'last_name', 'phone', 'email', 'vin',
            'has_insurance_claim', 'insurance_name', 'policy_number', 'referral_number',
            'has_extended_warranty'
        ]
        widgets = {
            # Use radio buttons for yes/no fields
            'impacting_driving': forms.CheckboxInput(),
            'is_quarter_damage': forms.RadioSelect(choices=[(True, 'Yes'), (False, 'No')]),
            'has_insurance_claim': forms.RadioSelect(choices=[(True, 'Yes'), (False, 'No')]),
            'has_extended_warranty': forms.RadioSelect(choices=[(True, 'Yes'), (False, 'No')]),
        }
