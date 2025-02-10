from django.db import models

# Create your models here.
from django.conf import settings
from a_users.models import Vehicle  # ensure you import the Vehicle model
from a_users.models import Customer

class InsuranceClaim(models.Model):
    customer = models.ForeignKey(
        Customer,
        related_name='insurance_claims',
        on_delete=models.CASCADE
    )
    insurance_name = models.CharField(max_length=100)
    insurance_id = models.CharField(max_length=50)  # your insurance ID field
    referral_number = models.CharField(max_length=50)
    dispatch_number = models.CharField(max_length=50)
    deductible = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='initiated')
    loss_date = models.DateField()
    assigned_date = models.DateField(null=True, blank=True)
    
    # Damage area choices
    DAMAGE_AREA_CHOICES = (
        ('windshield', 'Windshield'),
        ('front_door_glass', 'Front Door Glass'),
        ('rear_door_glass', 'Rear Door Glass'),
        ('back_glass', 'Back Glass'),
        ('quarter_glass', 'Quarter Glass'),
        ('vent_glass', 'Vent Glass'),
    )
    damage_area = models.CharField(max_length=20, choices=DAMAGE_AREA_CHOICES)
    
    # For damage areas (other than windshield and back_glass) add side choices:
    SIDE_CHOICES = (
        ('driver', 'Driver Side'),
        ('passenger', 'Passenger Side'),
    )
    # This field is optional – you can add validation in forms or model clean() methods.
    damage_side = models.CharField(max_length=10, choices=SIDE_CHOICES, null=True, blank=True)
    
    def __str__(self):
        return f"Claim {self.id} for {self.customer}"

class Quote(models.Model):
    claim = models.ForeignKey(
        InsuranceClaim,
        related_name='quotes',
        on_delete=models.CASCADE
    )
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # or import your Customer model if desired
        related_name='quotes',
        on_delete=models.CASCADE
    )
    vehicle = models.ForeignKey(
        Vehicle,
        related_name='quotes',
        on_delete=models.CASCADE
    )
    notes = models.TextField(blank=True, null=True)
    
    installation_labor = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    recalabration_costs = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    recalabration_type = models.CharField(max_length=50, blank=True, null=True)
    recalabration_description = models.TextField(blank=True, null=True)
    
    total_parts_costs = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_labor_costs = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gross_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Many-to-many relationship to Part through the join model QuotePart
    parts = models.ManyToManyField('Part', through='QuotePart', related_name='quotes')
    
    def __str__(self):
        return f"Quote for Claim {self.claim.id}"


class Part(models.Model):
    MAKE_CHOICES = [
        ('OEM', 'OEM'),
        ('aftermarket', 'Aftermarket'),
    ]
    
    part_number = models.CharField(max_length=50, unique=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    make = models.CharField(max_length=20, choices=MAKE_CHOICES)
    
    def __str__(self):
        return f"Part {self.part_number} ({self.make})"


class QuotePart(models.Model):
    quote = models.ForeignKey(
        Quote,
        related_name='quote_parts',
        on_delete=models.CASCADE
    )
    part = models.ForeignKey(
        Part,
        related_name='quote_parts',
        on_delete=models.CASCADE,
        null=True,  # Allow null values for now
        blank=True
    )
    # Additional fields (if needed)
    
    def __str__(self):
        return f"{self.part.part_number if self.part else 'No Part'} for Quote {self.quote.id}"


class Appointment(models.Model):
    claim = models.ForeignKey(
        InsuranceClaim,
        related_name='appointments',
        on_delete=models.CASCADE
    )
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='appointments',
        on_delete=models.CASCADE
    )
    vehicle = models.ForeignKey(
        Vehicle,
        related_name='appointments',
        on_delete=models.CASCADE
    )
    appointment_date = models.DateTimeField()
    service_location = models.CharField(max_length=100)
    
    def __str__(self):
        return f"Appointment for Claim {self.claim.id} on {self.appointment_date}"


class JobEntry(models.Model):
    # Step 1 – Damage Information
    DAMAGE_PIECE_CHOICES = [
        ('windshield', 'Windshield'),
        ('front_door_glass', 'Front Door Glass'),
        ('rear_door_glass', 'Rear Door Glass'),
        ('back_glass', 'Back Glass'),
        ('quarter_glass', 'Quarter Glass'),
        ('vent_glass', 'Vent Glass'),
    ]
    SIDE_CHOICES = [
        ('left', 'Left'),
        ('right', 'Right'),
    ]
    CAUSE_OF_DAMAGE_CHOICES = [
        ('foreign_object', 'Foreign Object'),
        ('vandalism', 'Vandalism'),
        ('unknown', 'Unknown'),
        ('other', 'Other'),
    ]
    
    damage_piece = models.CharField(
        max_length=20,
        choices=DAMAGE_PIECE_CHOICES,
        help_text="Select the piece of glass that was damaged."
    )
    # This field is only applicable for damage types that require a side selection.
    damage_side = models.CharField(
        max_length=10,
        choices=SIDE_CHOICES,
        blank=True,
        null=True,
        help_text="Select a side (left or right) if applicable."
    )
    cause_of_damage = models.CharField(
        max_length=20,
        choices=CAUSE_OF_DAMAGE_CHOICES,
        help_text="Select the cause of damage."
    )
    impacting_driving = models.BooleanField(
        help_text="Is this impacting your ability to drive?"
    )
    
    # Step 2 – Repair Option for Windshield Damage
    # Only applicable if damage_piece is 'windshield'
    is_quarter_damage = models.BooleanField(
        null=True,
        blank=True,
        help_text="Is the damage quarter sized or smaller? (Only applicable for windshields)"
    )
    
    # Step 3 – Customer Information
    first_name = models.CharField(max_length=50, help_text="Your first name")
    last_name = models.CharField(max_length=50, help_text="Your last name")
    phone = models.CharField(max_length=20, help_text="Your phone number")
    email = models.EmailField(blank=True, null=True, help_text="Your email (optional)")
    vin = models.CharField(
        max_length=17,
        help_text="Vehicle Identification Number (VIN)"
    )
    
    has_insurance_claim = models.BooleanField(
        default=False,
        help_text="Do you already have an insurance claim?"
    )
    insurance_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Insurance company name (if applicable)"
    )
    policy_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Insurance policy number (if applicable)"
    )
    referral_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Referral number (optional)"
    )
    
    has_extended_warranty = models.BooleanField(
        default=False,
        help_text="Have you purchased an extended warranty contract?"
    )
    
    # Record when the entry was created
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"JobEntry for {self.first_name} {self.last_name} - {self.damage_piece}"