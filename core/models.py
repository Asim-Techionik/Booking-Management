from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from django.utils.timezone import now
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
# from torch.fx.experimental.symbolic_shapes import definitely_false


class UserModelManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, phone_number, password=None, user_type='client', is_staff=False, is_superuser=False, **extra_fields):
        """
        Create and return a regular user with an email, password, and other fields.
        """
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, first_name=first_name, last_name=last_name, phone_number=phone_number, is_staff=is_staff, is_superuser=is_superuser, user_type=user_type, **extra_fields)
        user.set_password(password)  # Hash the password
        user.save(using=self._db)

        # Automatically create Client or Accessor entry
        if user_type == 'client':
            Client.objects.create(
                user=user,
                email=email,
                phone_number=phone_number,
                first_name=first_name,  # Explicitly assign first_name
                last_name=last_name  # Explicitly assign last_name
            )
        elif user_type == 'accessor':
            Accessor.objects.create(
                user=user,
                email=email,
                phone_number=phone_number,
                first_name=first_name,  # Explicitly assign first_name
                last_name=last_name  # Explicitly assign last_name
            )

        return user

    def create_superuser(self, email, first_name, last_name, phone_number, password=None, **extra_fields):
        """
        Create and return a superuser with an email, password, and other fields.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, first_name, last_name, phone_number, password, user_type='accessor', **extra_fields)


class UserModel(AbstractBaseUser, PermissionsMixin):
    USER_TYPE_CHOICES = (
        ('client', 'Client'),
        ('accessor', 'Accessor'),
    )

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    phone_number = models.CharField(
        max_length=15,
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$')]
    )
    password = models.CharField(max_length=255)
    user_type = models.CharField(max_length=255, choices=USER_TYPE_CHOICES, default='client')
    date_joined = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    preference = models.CharField(max_length=255, blank=True, null=True)
    home_county = models.CharField(max_length=255, blank=True, null=True)
    SEAI_registration = models.CharField(max_length=255, blank=True, null=True)
    SEAI_accessor_since = models.DateField(blank=True, null=True)
    professional_insurance_policy_holder = models.BooleanField(default=False)
    VAT_registered = models.BooleanField(default=False)
    domestic_or_commercial = models.CharField(
        max_length=10,
        choices=(('Domestic', 'Domestic'), ('Commercial', 'Commercial')),
        blank=True,
        null=True
    )

    objects = UserModelManager()  # Assign the custom manager here

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'phone_number']

    def save(self, *args, **kwargs):
        if self.password and not self.password.startswith('pbkdf2_sha256$'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email

class Client(models.Model):
    user = models.OneToOneField(UserModel, on_delete=models.CASCADE, related_name='client')
    address = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField()  # Duplicate field from UserModel
    phone_number = models.CharField()  # Duplicate field from UserModel
    first_name = models.CharField()  # Add first_name
    last_name = models.CharField()  # Add last_name

    def __str__(self):
        return f"Client: {self.user.email}"

class Accessor(models.Model):
    user = models.OneToOneField(UserModel, on_delete=models.CASCADE, related_name='accessor')
    address = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField()  # Duplicate field from UserModel
    phone_number = models.CharField()  # Duplicate field from UserModel
    first_name = models.CharField()  # Add first_name
    last_name = models.CharField()  # Add last_name



    def __str__(self):
        return f"Accessor: {self.user.email}"

class Job(models.Model):
    BUILDING_TYPES = [
        ('detached', 'Detached'),
        ('semi-detached', 'Semi-detached'),
        ('mid-terrace', 'Mid-terrace'),
        ('apartment', 'Apartment'),
        ('duplex', 'Duplex'),
        ('bunglow', 'Bunglow'),
        ('multi-unit', 'Multi-unit'),
        ('other', 'Other')
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in Progress', 'In Progress'),
        ('completed', 'Completed'),
    ]
    building_type = models.CharField(max_length=255, choices=BUILDING_TYPES)
    client = models.ForeignKey('Client', on_delete=models.CASCADE, related_name='job')

    status = models.CharField(max_length=255, choices=STATUS_CHOICES, default='pending')
    preferred_date = models.CharField(max_length=255)
    preferred_time = models.CharField(max_length=255)
    property_type = models.CharField(max_length=255)
    property_size = models.CharField(max_length=255)
    bedrooms = models.CharField(max_length=255)
    additional_features = models.CharField(max_length=255, blank=True, null=True)
    heat_pump_installed = models.CharField(max_length=255)
    county =models.CharField(max_length=255, blank=True, null=True)
    nearest_town = models.CharField(max_length=255)
    ber_purpose = models.CharField(max_length=255)
    lidar = models.FileField(upload_to='lidar_data/', blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(default=now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=255)
    email_address = models.CharField(max_length=255)
    mobile_number = models.CharField(max_length=255)


    def __str__(self):
        return self.BUILDING_TYPES


class Bid(models.Model):
    amount = models.FloatField(null=True, blank=True)
    availability = models.CharField(max_length=255)
    VAT_Registered = models.BooleanField(default=False)
    SEAI_Registered = models.BooleanField(default=False)
    insurance = models.BooleanField(default=False)
    assessor = models.ForeignKey('Accessor', on_delete=models.CASCADE, related_name='bids')
    job = models.ForeignKey('Job', on_delete=models.CASCADE, related_name='bids', blank=True, null=True)
    quote = models.ForeignKey('Quote', on_delete=models.CASCADE, related_name='bids', blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    def clean(self):
        # Ensure the job status is 'Pending'
        if self.job.status != 'pending':
            raise ValidationError(f"Bids cannot be placed on jobs that are {self.job.status}. Only jobs with 'Pending' status can receive bids.")

    def __str__(self):
        return f"Bid {self.id} by {self.assessor.user.email} for Job {self.job.building_type}"


class Notification(models.Model):
    message = models.TextField()
    notification_type = models.CharField(max_length=50)
    recipient = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name="notifications")
    status = models.CharField(max_length=50, choices=(
        ('unread', 'Unread'),
        ('read', 'Read'),
    ), default='unread')

    # For the sender, we allow both Client and Accessor
    sender_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    sender_object_id = models.PositiveIntegerField()
    sender = GenericForeignKey('sender_content_type', 'sender_object_id')
    created_at = models.DateTimeField(default=now)  # Add this field to store creation time

    def __str__(self):
        return f"Notification for {self.recipient.email} about {self.notification_type}"


class Project(models.Model):
    STATUS_CHOICES = [
        ('Not Started', 'Not Started'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
    ]

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='projects')  # Link to Job model
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Not Started')
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    # Link to Client and Accessor
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='projects')
    accessor = models.ForeignKey(Accessor, on_delete=models.CASCADE, related_name='projects')

    def __str__(self):
        return f"Project for Job: {self.job.building_type} (Status: {self.status})"


class Quote(models.Model):
    BUILDING_TYPES = [
        ('detached', 'Detached'),
        ('semi-detached', 'Semi-detached'),
        ('mid-terrace', 'Mid-terrace'),
        ('apartment', 'Apartment'),
        ('duplex', 'Duplex'),
        ('bunglow', 'Bunglow'),
        ('multi-unit', 'Multi-unit'),
        ('other', 'Other')
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in Progress', 'In Progress'),
        ('completed', 'Completed'),
    ]
    building_type = models.CharField(max_length=50, choices=BUILDING_TYPES, blank=True, null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    preferred_date = models.CharField(max_length=255)
    preferred_time = models.CharField(max_length=255)
    property_type = models.CharField(max_length=255)
    property_size = models.CharField(max_length=255)
    bedrooms = models.CharField(max_length=255)
    additional_features = models.CharField(max_length=255, blank=True, null=True)
    heat_pump_installed = models.CharField(max_length=255)
    county = models.CharField(max_length=255)
    nearest_town = models.CharField(max_length=255)
    ber_purpose = models.CharField(max_length=255)
    lidar = models.FileField(upload_to='lidar_data/', blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(default=now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=255)
    email_address = models.CharField(max_length=255)
    mobile_number = models.CharField(max_length=255)


    def __str__(self):
        return f"Quote request for {self.property_type} in {self.county}"

class Payment(models.Model):
    assessor = models.ForeignKey('Accessor', on_delete=models.CASCADE, related_name='payments')
    job = models.ForeignKey('Job', on_delete=models.CASCADE, related_name='payments')
    bid = models.ForeignKey('Bid', on_delete=models.CASCADE, related_name='payments')
    amount = models.PositiveIntegerField()  # Amount in cents (we will auto-generate this)
    currency = models.CharField(max_length=10, default='usd')
    stripe_payment_id = models.CharField(max_length=255, unique=True)  # To store Stripe's payment session ID
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.amount:
            # Set the amount from the related Bid's amount (converted to cents)
            self.amount = int(self.bid.amount * 100)  # Assuming the bid amount is in dollars
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Payment of {self.amount} {self.currency} for Job {self.job.building_type}"


class Assesment(models.Model):
    quote = models.ForeignKey(Quote, on_delete=models.CASCADE, related_name="assessments", null=True, blank=True)
    project =models.ForeignKey(Project, on_delete=models.CASCADE, related_name='assesments', null=True, blank=True)
    #Link to Client and Accessor
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='assesments', null=True, blank=True)
    accessor = models.ForeignKey(Accessor, on_delete=models.CASCADE, related_name='assesments', null=True, blank=True)

    assessor_name = models.CharField(blank=True, null=True, max_length=255)
    ber_reg_no = models.CharField(blank=True, null=True, max_length=255)
    survey_date = models.CharField(blank=True, null=True)

    # Property details
    num_storeys = models.IntegerField(null=True, blank=True)
    num_bedrooms = models.IntegerField(null=True, blank=True)
    num_extensions = models.CharField(default=False)
    property_address = models.CharField(null=True, blank=True, max_length=255)
    eircode = models.CharField(null=True, blank=True, max_length=255)
    mprn = models.CharField(null=True, blank=True, max_length=255)

    #dwelling_type
    # Type of Rating
    detached_house = models.BooleanField(default=False)
    semi_detached_house = models.BooleanField(default=False)
    end_of_terrace = models.BooleanField(default=False)
    mid_terrace = models.BooleanField(default=False)
    ground_floor_apartment = models.BooleanField(default=False)
    mid_floor_apartment = models.BooleanField(default=False)
    top_floor_apartment = models.BooleanField(default=False)
    basement_apartment = models.BooleanField(default=False)
    maisonette = models.BooleanField(default=False)

    #Age: Dwelling
    # Age categories
    pre_1900 = models.BooleanField(default=False)
    between_1900_and_1929 = models.BooleanField(default=False)
    between_1930_and_1949 = models.BooleanField(default=False)
    between_1950_and_1966 = models.BooleanField(default=False)
    between_1967_and_1977 = models.BooleanField(default=False)
    between_1978_and_1982 = models.BooleanField(default=False)
    between_1983_and_1993 = models.BooleanField(default=False)
    between_1994_and_1999 = models.BooleanField(default=False)
    from_2000_onwards = models.BooleanField(default=False)


    #age_extension_1
    xpre_1900 = models.BooleanField(default=False)
    xbetween_1900_and_1929 = models. BooleanField(default=False)
    xbetween_1930_and_1949 = models.BooleanField(default=False)
    xbetween_1950_and_1966 = models.BooleanField(default=False)
    xbetween_1967_and_1977 = models.BooleanField(default=False)
    xbetween_1978_and_1982 = models.BooleanField(default=False)
    xbetween_1983_and_1993 = models.BooleanField(default=False)
    xbetween_1994_and_1999 = models.BooleanField(default=False)
    xfrom_2000_onwards = models.BooleanField(default=False)


    #age_extension_2
    xxpre_1900 = models.BooleanField(default=False)
    xxbetween_1900_and_1929 = models.BooleanField(default=False)
    xxbetween_1930_and_1949 = models.BooleanField(default=False)
    xxbetween_1950_and_1966 = models.BooleanField(default=False)
    xxbetween_1967_and_1977 = models.BooleanField(default=False)
    xxbetween_1978_and_1982 = models.BooleanField(default=False)
    xxbetween_1983_and_1993 = models.BooleanField(default=False)
    xxbetween_1994_and_1999 = models.BooleanField(default=False)
    xxfrom_2000_onwards = models.BooleanField(default=False)

    #type of rating
    new_final_dwelling = models.BooleanField(default=False)
    existing_dwelling = models.BooleanField(default=False)
    # Purpose of rating
    new_owner_occupation = models.BooleanField(default=False)
    sale = models.BooleanField(default=False)
    private_letting = models.BooleanField(default=False)
    social_housing_letting = models.BooleanField(default=False)
    grant_support = models.BooleanField(default=False)
    major_renovation = models.BooleanField(default=False)
    purpose_of_rating_other = models.BooleanField(default=False)
    purpose_of_rating_other_text = models.CharField(null=True, blank=True, max_length=255)

    #Wall construction main wall
    stone = models.BooleanField(default=False)
    solid_brick = models.BooleanField(default=False)
    cavity = models.BooleanField(default=False)
    solid_concrete = models.BooleanField(default=False)
    hollow_block = models.BooleanField(default=False)
    timber_frame = models.BooleanField(default=False)
    other_unknown = models.BooleanField(default=False)
    other_unknow_text = models.CharField(null=True, blank=True, max_length=255)
    insulation_thickness_observable = models.CharField(null=True, blank=True, max_length=255)

    # Roof Construction: Main Dwelling
    pitched_insulation_btw_joists = models.BooleanField(default=False)
    pitched_insulation_in_rafters = models.BooleanField(default=False)
    Flat_insulation_integral = models.BooleanField(default=False)
    room_in_roof = models.BooleanField(default=False)
    no_heat_loss_roof = models.BooleanField(default=False)
    roof_Construction_Other =models.BooleanField(default=False)
    roof_Construction_Other_text = models.CharField(null=True, blank=True, max_length=255)
    #Roof insulations : Main Dwelling
    thinkness = models.FloatField(blank = True, null = True)
    roof_construction_unknown = models.CharField(blank = True, null = True)
    fibre = models.BooleanField(default=False)
    warmcell = models.BooleanField(default=False)
    eps = models.BooleanField(default=False)
    dense = models.BooleanField(default=False)

    #Ground Floor Construction: Main Dwelling
    solid = models.BooleanField(default=False)
    suspended = models.BooleanField(default=False)
    above_unheated_basement = models.BooleanField(default=False)
    heated_basement = models.BooleanField(default=False)
    no_heat_loss_ground_floor = models.BooleanField(default=False)
    sealed = models.BooleanField(default=False)
    ground_Floor_Dwelling_other = models.BooleanField(default=False)
    #floor insulation
    floor_insulation = models.CharField(blank = True, null = True, max_length=255)
    ground_Floor_insulation_none = models.BooleanField(default=False)
    #type of insulation
    Ground_Floor_Construction_Main_Dwelling_eps = models.BooleanField(default=False)
    Ground_Floor_Construction_Main_Dwelling_min_fibre = models.BooleanField(default=False)
    Ground_Floor_Construction_Main_Dwelling_dense = models.BooleanField(default=False)
    Ground_Floor_Construction_Main_Dwelling_unknow = models.BooleanField(default=False)

    # Wall construction main wall TYPE 2
    type_2_stone = models.BooleanField(default=False)
    Type_2_solid_brick = models.BooleanField(default=False)
    type_2_cavity = models.BooleanField(default=False)
    type_2_solid_concrete = models.BooleanField(default=False)
    type_2_hollow_block = models.BooleanField(default=False)
    type_2_timber_frame = models.BooleanField(default=False)
    type_2_other_unknown = models.BooleanField(default=False)
    type_2_other_text = models.CharField(null=True, blank=True, max_length=255)
    type_2_insulation_thickness_observable = models.CharField(null=True, blank=True, max_length=255)

    # Roof Construction: Type 2
    type_2_pitched_insulation_btw_joists = models.BooleanField(default=False)
    type_2_pitched_insulation_in_rafters = models.BooleanField(default=False)
    type_2_Flat_insulation_integral = models.BooleanField(default=False)
    type_2_room_in_roof = models.BooleanField(default=False)
    type_2_no_heat_loss_roof = models.BooleanField(default=False)
    type_2_roof_Construction_Other = models.BooleanField(default=False)
    type_2_roof_Construction_Other_text = models.CharField(null=True, blank=True, max_length=255)
    # Roof insulations : Main Dwelling TYPE 2
    type_2_thinkness = models.FloatField(blank=True, null=True)
    type_2_roof_construction_unknown = models.CharField(blank=True, null=True)
    type_2_fibre = models.BooleanField(default=False)
    type_2_warmcell = models.BooleanField(default=False)
    type_2_eps = models.BooleanField(default=False)
    type_2_dense = models.BooleanField(default=False)

    # Ground Floor Construction: Main Dwelling
    type_2_solid = models.BooleanField(default=False)
    type_2_suspended = models.BooleanField(default=False)
    type_2_above_unheated_basement = models.BooleanField(default=False)
    type_2_heated_basement = models.BooleanField(default=False)
    type_2_no_heat_loss_ground_floor = models.BooleanField(default=False)
    type_2_sealed = models.BooleanField(default=False)
    type_2_ground_Floor_Dwelling_other = models.BooleanField(default=False)
    # floor insulation
    type_2_floor_insulation = models.CharField(blank=True, null=True, max_length=255)
    type_2_ground_Floor_insulation_none = models.BooleanField(default=False)
    # type of insulation
    type_2_ground_floor_construction_main_dwelling_eps = models.BooleanField(default=False)
    type_2_ground_floor_construction_main_dwelling_min_fibre = models.BooleanField(default=False)
    type_2_ground_floor_construction_main_dwelling_dense = models.BooleanField(default=False)
    type_2_ground_floor_construction_main_dwelling_unknow = models.BooleanField(default=False)

    # Wall construction main wall TYPE 3
    type_3_stone = models.BooleanField(default=False)
    Type_3_solid_brick = models.BooleanField(default=False)
    type_3_cavity = models.BooleanField(default=False)
    type_3_solid_concrete = models.BooleanField(default=False)
    type_3_hollow_block = models.BooleanField(default=False)
    type_3_timber_frame = models.BooleanField(default=False)
    type_3_ther_unknown = models.BooleanField(default=False)
    type_3_ther_unknown_text = models.CharField(null=True, blank=True, max_length=255)
    type_3_insulation_thickness_observable = models.CharField(null=True, blank=True, max_length=255)

    # Roof Construction: Type 3
    type_3_pitched_insulation_btw_joists = models.BooleanField(default=False)
    type_3_pitched_insulation_in_rafters = models.BooleanField(default=False)
    type_3_Flat_insulation_integral = models.BooleanField(default=False)
    type_3_room_in_roof = models.BooleanField(default=False)
    type_3_no_heat_loss_roof = models.BooleanField(default=False)
    type_3_roof_Construction_Other = models.BooleanField(default=False)
    type_3_roof_Construction_Other_text = models.CharField(null=True, blank=True, max_length=255)
    # Roof insulations : Main Dwelling TYPE 3
    type_3_thinkness = models.FloatField(blank=True, null=True)
    type_3_roof_construction_unknown = models.CharField(blank=True, null=True)
    type_3_fibre = models.BooleanField(default=False)
    type_3_warmcell = models.BooleanField(default=False)
    type_3_eps = models.BooleanField(default=False)
    type_3_dense = models.BooleanField(default=False)

    # Ground Floor Construction: Main Dwelling TYPE 3
    type_3_solid = models.BooleanField(default=False)
    type_3_suspended = models.BooleanField(default=False)
    type_3_above_unheated_basement = models.BooleanField(default=False)
    type_3_heated_basement = models.BooleanField(default=False)
    type_3_no_heat_loss_ground_floor = models.BooleanField(default=False)
    type_3_sealed = models.BooleanField(default=False)
    type_3_ground_Floor_Dwelling_other = models.BooleanField(default=False)
    # floor insulation
    type_3_floor_insulation = models.CharField(blank=True, null=True, max_length=255)
    type_3_ground_Floor_insulation_none = models.BooleanField(default=False)
    # type of insulation
    type_3_ground_floor_construction_main_dwelling_eps = models.BooleanField(default=False)
    type_3_ground_floor_construction_main_dwelling_min_fibre = models.BooleanField(default=False)
    type_3_ground_floor_construction_main_dwelling_dense = models.BooleanField(default=False)
    type_3_ground_floor_construction_main_dwelling_unknow = models.BooleanField(default=False)

    # Wall construction main wall TYPE 3
    type_4_stone = models.BooleanField(default=False)
    Type_4_solid_brick = models.BooleanField(default=False)
    type_4_cavity = models.BooleanField(default=False)
    type_4_solid_concrete = models.BooleanField(default=False)
    type_4_hollow_block = models.BooleanField(default=False)
    type_4_timber_frame = models.BooleanField(default=False)
    type_4_ther_unknown = models.BooleanField(default=False)
    type_4_ther_unknown_text = models.CharField(null=True, blank=True, max_length=255)
    type_4_insulation_thickness_observable = models.CharField(null=True, blank=True, max_length=255)

    # Roof Construction: Type 3
    type_4_pitched_insulation_btw_joists = models.BooleanField(default=False)
    type_4_pitched_insulation_in_rafters = models.BooleanField(default=False)
    type_4_Flat_insulation_integral = models.BooleanField(default=False)
    type_4_room_in_roof = models.BooleanField(default=False)
    type_4_no_heat_loss_roof = models.BooleanField(default=False)
    type_4_roof_Construction_Other = models.BooleanField(default=False)
    type_4_roof_Construction_Other_text = models.CharField(null=True, blank=True, max_length=255)
    # Roof insulations : Main Dwelling TYPE 3
    type_4_thinkness = models.FloatField(blank=True, null=True)
    type_4_roof_construction_unknown = models.CharField(blank=True, null=True)
    type_4_fibre = models.BooleanField(default=False)
    type_4_warmcell = models.BooleanField(default=False)
    type_4_eps = models.BooleanField(default=False)
    type_4_dense = models.BooleanField(default=False)

    # Ground Floor Construction: Main Dwelling TYPE 3
    type_4_solid = models.BooleanField(default=False)
    type_4_suspended = models.BooleanField(default=False)
    type_4_above_unheated_basement = models.BooleanField(default=False)
    type_4_heated_basement = models.BooleanField(default=False)
    type_4_no_heat_loss_ground_floor = models.BooleanField(default=False)
    type_4_sealed = models.BooleanField(default=False)
    type_4_ground_Floor_Dwelling_other = models.BooleanField(default=False)
    # floor insulation
    type_4_floor_insulation = models.CharField(blank=True, null=True, max_length=255)
    type_4_ground_Floor_insulation_none = models.BooleanField(default=False)
    # type of insulation
    type_4_ground_floor_construction_main_dwelling_eps = models.BooleanField(default=False)
    type_4_ground_floor_construction_main_dwelling_min_fibre = models.BooleanField(default=False)
    type_4_ground_floor_construction_main_dwelling_dense = models.BooleanField(default=False)
    type_4_ground_floor_construction_main_dwelling_unknow = models.BooleanField(default=False)


    #########################PAGE 3###################################
    #VENTILATION FACTORS
    draught_lobby_on_main_entrance = models.CharField(blank=True, null=True, max_length=255)
    pressure_test_results_available = models.BooleanField(blank=True, null=True)
    if_yes_enter_adjusted_results = models.CharField(blank=True, null=True)
    is_there_uninsulated_ductng_on_mvhr = models.CharField(blank=True, null=True, max_length=255)
    number_of_sides_sheltered = models.CharField(blank=True, null=True)
    pressure_test_resut_reference_number = models.CharField(blank=True, null=True, max_length=255)
    natural_ventilation = models.BooleanField(default=False)
    positive_input_ventilation_from_loft = models.BooleanField(default=False)
    positive_input_ventilation_from_outside = models.BooleanField(default=False)
    whole_house_extract_ventilation = models.BooleanField(default=False)
    balanceed_whole_mechanical_ventilation = models.BooleanField(default=False)
    exhaust_air_heat_pump = models.BooleanField(default=False)
    air_flow_rate_to_eahp = models.BooleanField(default=False)
    mech_ventilation_system_details = models.CharField(blank=True, null=True, max_length=255),


    #LIGHTING SUMMARY
    linear_flourescent = models.IntegerField(blank=True, null=True)
    led = models.IntegerField(blank=True, null=True)
    hologen_lv = models.IntegerField(blank=True, null=True)
    cfl = models.IntegerField(blank=True, null=True)
    halogen_lamps = models.IntegerField(blank=True, null=True)
    incadescent_unknown = models.CharField(blank=True, null=True, max_length=255)


    #SPACE HEATING SYSTEM (GENERAL INFORMATION)

    #PRIMARY HEATING SYETEM
    radiator_system_primary = models.BooleanField(default=False)
    storage_heaters_primary = models.BooleanField(default=False)
    underfloor_primary = models.BooleanField(default=False)
    warm_air_primary = models.BooleanField(default=False)
    room_heaters_only_primary = models.BooleanField(default=False)
    communtiy_primary = models.BooleanField(default=False)
    fan_coil_radiator_primay = models.BooleanField(default=False)
    other_primary_heating = models.BooleanField(default=False)
    other_primary_heating_text = models.CharField(null=True, blank=True, max_length=255)

    #SECONDARY HEATING SYSTEM
    radiator_system_secondary = models.BooleanField(default=False)
    storage_heaters_secondary = models.BooleanField(default=False)
    underfloor_secondary = models.BooleanField(default=False)
    warm_air_secondary = models.BooleanField(default=False)
    room_heaters_only_secondary = models.BooleanField(default=False)
    communtiy_secondary = models.BooleanField(default=False)
    fan_coil_radiator_secondary = models.BooleanField(default=False)
    other_secondary_heating = models.BooleanField(default=False)
    other_secondary_heating_text = models.CharField(null=True, blank=True, max_length=255)

    #PRIMARY HEATING FUEL
    main_gas = models.BooleanField(default=False)
    bulk_lpg = models.BooleanField(default=False)
    bottled_lpg = models.BooleanField(default=False)
    heating_oil = models.BooleanField(default=False)
    electricity = models.BooleanField(default=False)
    heat_from_chp = models.BooleanField(default=False)
    bioethanol = models.BooleanField(default=False)
    housecoal = models.BooleanField(default=False)
    anthracite = models.BooleanField(default=False)
    smokeless = models.BooleanField(default=False)
    peat_briquettes = models.BooleanField(default=False)
    sod_peat = models.BooleanField(default=False)
    wood_pellets = models.BooleanField(default=False)
    wood_chips = models.BooleanField(default=False)
    biodiesel = models.BooleanField(default=False)
    other_heating_system = models.BooleanField(default=False)
    other_heating_system_text = models.CharField(null=True, blank=True, max_length=255)

    # SECONDARY HEATING FUEL
    main_gas_s = models.BooleanField(default=False)
    bulk_lpg_s = models.BooleanField(default=False)
    bottled_lpg_s = models.BooleanField(default=False)
    heating_oil_s = models.BooleanField(default=False)
    electricity_s = models.BooleanField(default=False)
    heat_from_chp_s = models.BooleanField(default=False)
    bioethanol_s = models.BooleanField(default=False)
    housecoal_s = models.BooleanField(default=False)
    anthracite_s = models.BooleanField(default=False)
    smokeless_s = models.BooleanField(default=False)
    peat_briquettes_s = models.BooleanField(default=False)
    sod_peat_s = models.BooleanField(default=False)
    wood_pellets_s = models.BooleanField(default=False)
    wood_chips_s = models.BooleanField(default=False)
    biodiesel_s = models.BooleanField(default=False)
    other_heating_system_s = models.BooleanField(default=False)
    other_heating_system_s_text = models.CharField(null=True, blank=True, max_length=255)

    #GAS_OIL_LPG BOILERS (PRIMAR/SECONDARY)
    gas_oil_lpg = models.CharField(null=True, blank=True, max_length=255)
    #BOILER TYPE
    standard = models.BooleanField(default=False)
    Combi = models.BooleanField(default=False)
    condensing = models.BooleanField(default=False)
    back_boiler = models.BooleanField(default=False)
    cpsu = models.BooleanField(default=False)
    range_cooker = models.BooleanField(default=False)
    single_burner = models.BooleanField(default=False)
    twin_burner = models.BooleanField(default=False)
    #FLUE TYPE
    open = models.BooleanField(default=False)
    balanced = models.BooleanField(default=False)
    fan_assisted = models.BooleanField(default=False)
    #AGE
    pre_1998_or_later = models.BooleanField(default=False)
    pre_1998 = models.BooleanField(default=False)
    oil_pre_1985 = models.BooleanField(default=False)
    gas_lpg_pre_1979 = models.BooleanField(default=False)
    #MOUNTING
    wall = models.BooleanField(default=False)
    floor = models.BooleanField(default=False)
    #IGNITION
    auto = models.BooleanField(default=False)
    permanent_pilot = models.BooleanField(default=False)
    gas_oil_manufacturer = models.CharField(blank=True, null=True, max_length=255)

    #SOLID FUEL BOILERS
    solid_fuel_boilers = models.CharField(blank=True, null=True, max_length=255)
    open_fire_back_boiler = models.BooleanField(default=False)
    closed_room_heater_back_boiler = models.BooleanField(default=False)
    grate = models.CharField(choices=[('Rectangular', 'rectangular'), ('Trapezium', 'trapezium')])
    manual_feed_boiler = models.CharField(blank=True, null=True, max_length=255)
    auto_feed_boiler = models.BooleanField(default=False)
    mf_af_boiler_heated_space = models.BooleanField(default=False)
    ####RANGE COOKER BOILER WITH
    interal_oven = models.BooleanField(default=False)
    independant_oven = models.BooleanField(default=False)
    biomass_boiler = models.BooleanField(default=False)
    wood_chips_pellet_boiler = models.BooleanField(default=False)
    solid_fuel_manufacturer = models.CharField(default=False)


    #ELECTRIC BOILERS
    electric_boilers = models.CharField(blank=True, null=True, max_length=255)
    direct_acting = models.BooleanField(default=False)
    dry_core = models.BooleanField(default=False)
    electric_boilers_cpsu = models.BooleanField(default=False)
    water_storage = models.BooleanField(default=False)
    dry_core_water_storage = models.BooleanField(default=False)

    comments_on_heating_system = models.CharField(blank=True, null=True, max_length=255)

    #ELECTRIC STORAGE HEATER
    electric_storage_heater = models.CharField(blank=True, null=True, max_length=255)
    modern_slimeline = models.BooleanField(default=False)
    converter = models.BooleanField(default=False)
    electric_storage_heater_fan_assisted = models.BooleanField(default=False)
    old_pre_1980_volume = models.BooleanField(default=False)
    integrated_storage_direct_acting = models.BooleanField(default=False)
    ##CONTROL OPTIONS
    manual_charge_control = models.BooleanField(default=False)
    automatic_weather_dependant = models.BooleanField(default=False)
    celect_type = models.BooleanField(default=False)

    ##GAS ROOM HEATERS
    gas_room_heaters = models.CharField(blank=True, null=True, max_length=255)
    gas_room_pre_1980 = models.BooleanField(default=False)
    coal_effect_sealed_flue = models.BooleanField(default=False)
    coal_effect_open_to_chimney = models.BooleanField(default=False)
    flueless = models.BooleanField(default=False)
    gas_room_condensing = models.BooleanField(default=False)
    gas_room_back_boiler = models.BooleanField(default=False)
    gas_room_other = models.BooleanField(default=False)
    ##FRONT
    open_fronted = models.BooleanField(default=False)
    glass_fronted = models.BooleanField(default=False)
    ##FLUE TYPE
    flue_type_open = models.BooleanField(default=False)
    flue_type_balanced = models.BooleanField(default=False)
    flue_type_fan_assisted = models.BooleanField(default=False)

    ##WARM AIR SYSTEM
    warm_air_syetem = models.CharField(blank=True, null=True, max_length=255)
    #Ducted or stud Ducted
    ducted_or_stud_ducted_on_off = models.BooleanField(default=False)
    ducted_or_stud_ducted_modulating = models.BooleanField(default=False)
    ###OTHER FEATURES
    features_fan_assited = models.BooleanField(default=False)
    features_fan_condensing = models.BooleanField(default=False)
    features_fan_flue_heat_recovery = models.BooleanField(default=False)
    ###OTHER TYPE
    room_heater_with_in_floor_ducts = models.BooleanField(default=False)
    electric_electricaire = models.BooleanField(default=False)

    ####OIL ROOM HEATERS
    oil_room_heaters = models.CharField(blank=True, null=True, max_length=255)
    room_heater_range = models.BooleanField(default=False)
    room_heater_range_boiler = models.BooleanField(default=False)
    ##AGE
    oil_room_heaters_pre_2000 = models.BooleanField(default=False)
    oil_room_heaters_2000_later = models.BooleanField(default=False)

    ####SOLID FUEL ROOM HEATERS
    solid_fuel_room_heaters = models.CharField(blank=True, null=True, max_length=255)
    open_fire_in_grate = models.BooleanField(default=False)
    solid_fuel_open_fire_back_boiler = models.BooleanField(default=False)
    closed_room_heater = models.BooleanField(default=False)
    closed_room_heater_with_back_boiler = models.BooleanField(default=False)
    stove = models.BooleanField(default=False)
    flueless_bioethanol = models.BooleanField(default=False)


    ####HEAT PUMP
    heat_pump = models.CharField(blank=True, null=True, max_length=255)
    air_to_air = models.BooleanField(default=False)
    air_to_water = models.BooleanField(default=False)
    gas_fired_ground_watered = models.BooleanField(default=False)
    ground_to_air = models.BooleanField(default=False)
    ground_to_water = models.BooleanField(default=False)
    water_to_air = models.BooleanField(default=False)
    water_to_water = models.BooleanField(default=False)
    gas_fired_air_source = models.BooleanField(default=False)
    heat_pump_includes_auxiliary_electric_heaters = models.BooleanField(default=False)
    heat_pump_manufacturer = models.CharField(blank=True, null=True, max_length=255)

    ##ELECTRIC ROOM HEATERS
    electric_room_heater = models.CharField(blank=True, null=True, max_length=255)
    panel_converter_radiant_heater = models.BooleanField(default=False)
    fan_heater = models.BooleanField(default=False)
    secondary_heating_manufacturer = models.BooleanField(default=False)

    ##INDIVIDUAL CHP
    individual_chp = models.BooleanField(default=False)
    percentage_heat_from_chp = models.IntegerField(blank=True, null=True,)
    ##CHP EFFICIENCIES
    electrical = models.IntegerField(blank=True, null=True,)
    thermal = models.IntegerField(blank=True, null=True,)
    fuel = models.CharField(blank=True, null=True,)

##############################PAGE 4######################################
    ##HEATING SYSTEM
    ##PRIMARY HOT WATER SYSTEM
    from_primamry_heating_system = models.BooleanField(default=False)
    electric_immersion = models.BooleanField(default=False)
    electric_instantaneoues = models.BooleanField(default=False)
    gas_instant_single_point = models.BooleanField(default=False)
    gas_instant_multi_point = models.BooleanField(default=False)
    gas_circulator_pre_1998 = models.BooleanField(default=False)
    keep_hot_facility_controlled_by = models.BooleanField(default=False)
    less_than_55_liters = models.BooleanField(default=False)
    greater_than_50 = models.BooleanField(default=False)
    backboiler_kitchen_rage = models.BooleanField(default=False)
    primamry_heating_gas = models.BooleanField(default=False)
    primamry_heating_oil = models.BooleanField(default=False)
    primamry_heating_sf = models.BooleanField(default=False)
    primamry_heating_gas_circulator_1998_later = models.BooleanField(default=False)
    time_clock = models.BooleanField(default=False)
    no_time_clock = models.BooleanField(default=False)


    #####HOT WATER CYLINDER, INSULATION, CONTROLS
    hot_water_cylinder = models.CharField(blank=True, null=True, max_length=255)
    no_access = models.BooleanField(default=False)
    Capacity_liters_dimensions = models.CharField(blank=True, null=True, max_length=50)
    no_insulations = models.BooleanField(default=False)
    laggin_jacket = models.BooleanField(default=False)
    factory_fitted = models.BooleanField(default=False)
    hot_water_cylinder_pipework_insulated = models.BooleanField(default=False)
    insulation_thickness = models.CharField(blank=True, null=True, max_length=50)
    #####CONTROLS############
    cylinder_thermostat = models.BooleanField(default=False)
    independant_timeer = models.BooleanField(default=False)
    storage_is_outdoors = models.BooleanField(default=False)

    ############SOLAR WATER HEATING SYSTEM####################################
    solar_water_haeting = models.CharField(blank=True, null=True, max_length=255)
    evacuated_tube = models.BooleanField(default=False)
    flat_plate_glazed = models.BooleanField(default=False)
    flat_plate_unglazed = models.BooleanField(default=False)
    solar_collector_area = models.CharField(blank=True, null=True, max_length=50)
    very_little_less_20_per = models.BooleanField(default=False)
    significant_sixty_to_eighty_per = models.BooleanField(default=False)

    dedicated_solar_storage_volume = models.CharField(blank=True, null=True, max_length=50)
    contained_within_combained_cylinder = models.BooleanField(default=False)
    contained_within_separate_cylinder = models.BooleanField(default=False)

    orientation = models.CharField(blank=True, null=True, max_length=50)
    tilt = models.CharField(blank=True, null=True, max_length=50)

    area_is_gross = models.BooleanField(default=False)
    area_is_aperture = models.BooleanField(default=False)
    modest_twenty_to_sixty = models.BooleanField(default=False)
    heavy_more_than_eighty = models.BooleanField(default=False)

    solar_panel_make_model = models.CharField(blank=True, null=True, max_length=100)

    #####SUPPLYMENTARY_SUMMER_HOT_WATER##################
    supplementary_hot_water_not_applicable = models.BooleanField(default=False)
    electric_heater_present_for_supplementary = models.BooleanField(default=False)

    Comments_on_water_heating = models.CharField(blank=True, null=True, max_length=200)

    #Shower and BATHS#

    shower_dwelling = models.BooleanField(default=False)
    shower_water_use_target = models.BooleanField(default=False)

    shower_1_flow_rate_known = models.CharField(blank=True, null=True, max_length=100)
    shower_1_type = models.CharField(blank=True, null=True, max_length=100)
    shower_1_flow_restrictor = models.CharField(blank=True, null=True, max_length=100)
    Shower_1_flow_rate = models.CharField(blank=True, null=True, max_length=100)
    Shower_1_whhr_1 = models.CharField(blank=True, null=True, max_length=100)
    Shower_1_whhr_2 = models.CharField(blank=True, null=True, max_length=100)

    shower_2_flow_rate_known = models.CharField(blank=True, null=True, max_length=100)
    shower_2_type = models.CharField(blank=True, null=True, max_length=100)
    shower_2_flow_restrictor = models.CharField(blank=True, null=True, max_length=100)
    Shower_2_flow_rate = models.CharField(blank=True, null=True, max_length=100)
    Shower_2_whhr_1 = models.CharField(blank=True, null=True, max_length=100)
    Shower_2_whhr_2 = models.CharField(blank=True, null=True, max_length=100)

    shower_3_flow_rate_known = models.CharField(blank=True, null=True, max_length=100)
    shower_3_type = models.CharField(blank=True, null=True, max_length=100)
    shower_3_flow_restrictor = models.CharField(blank=True, null=True, max_length=100)
    Shower_3_flow_rate = models.CharField(blank=True, null=True, max_length=100)
    Shower_3_whhr_1 = models.CharField(blank=True, null=True, max_length=100)
    Shower_3_whhr_2 = models.CharField(blank=True, null=True, max_length=100)

    shower_4_flow_rate_known = models.CharField(blank=True, null=True, max_length=100)
    shower_4_type = models.CharField(blank=True, null=True, max_length=100)
    shower_4_flow_restrictor = models.CharField(blank=True, null=True, max_length=100)
    Shower_4_flow_rate = models.CharField(blank=True, null=True, max_length=100)
    Shower_4_whhr_1 = models.CharField(blank=True, null=True, max_length=100)
    Shower_4_whhr_2 = models.CharField(blank=True, null=True, max_length=100)

    shower_5_flow_rate_known = models.CharField(blank=True, null=True, max_length=100)
    shower_5_type = models.CharField(blank=True, null=True, max_length=100)
    shower_5_flow_restrictor = models.CharField(blank=True, null=True, max_length=100)
    Shower_5_flow_rate = models.CharField(blank=True, null=True, max_length=100)
    Shower_5_whhr_1 = models.CharField(blank=True, null=True, max_length=100)
    Shower_5_whhr_2 = models.CharField(blank=True, null=True, max_length=100)
    ###################### Page 5 ################################

    #HEATING CONTROL #####
    no_controls = models.BooleanField(default=False)
    programmer_time_clock = models.BooleanField(default=False)
    room_thermostat = models.BooleanField(default=False)
    number = models.CharField(blank=True, null=True, max_length=50)
    trvs = models.BooleanField(default=False)
    per_rads_trvs = models.CharField(blank=True, null=True, max_length=50)
    bypass = models.BooleanField(default=False)
    load_compensator = models.BooleanField(default=False)
    weather_compersator = models.BooleanField(default=False)
    full_zone_control = models.BooleanField(default=False)
    boiler_energy_management = models.BooleanField(default=False)
    delay_start_thermostat = models.BooleanField(default=False)
    boiler_interlock = models.BooleanField(default=False)
    appliances_thermostat = models.BooleanField(default=False)
    appliances_time_clock = models.BooleanField(default=False)

    ###HEATING SYSTEM CONTROLS##########
    in_insulated_timber_floor = models.BooleanField(default=False)
    in_screed = models.BooleanField(default=False)
    in_concrete = models.BooleanField(default=False)
    whole_house_UFH = models.BooleanField(default=False)
    partial_UFH_including_living_area = models.BooleanField(default=False)
    partial_UFH_not_including_living_area = models.BooleanField(default=False)

    #######PUMPS##########
    central_heating_pumps_for_space_heating = models.IntegerField(blank = True, null = True)
    central_heating_pumps_outdoors = models.IntegerField(blank = True, null = True)
    oil_boiler_fuel_pumps = models.IntegerField(blank = True, null = True)
    oil_fuel_pumps_outdoors = models.IntegerField(blank = True, null = True)
    gas_boiler_flue_fans = models.IntegerField(blank = True, null = True)

    #######COMMENTS ON HEATING CONTROLS#########
    comments_on_heating_controls = models.BooleanField(default=False)


    ########GROUP HEATING############
    #####DISTRIBUTION LOSS FACTOR AND CHARGE METHOD############
    pre_1991_full_flow_mid_high_temp_not_pre_insulated = models.BooleanField(default=False)
    pre_1991_full_flow_low_temp_pre_insulated = models.BooleanField(default=False)
    from_1991_or_later_variable_flow_mid_temp_pre_insulated = models.BooleanField(default=False)
    from_1991_or_later_variable_flow_low_temp_pre_insulated = models.BooleanField(default=False)
    consumption_charged_flat_rate = models.BooleanField(default=False)
    linked_to_use = models.BooleanField(default=False)

    ###########HEATING SYSTEM #1####################
    efficiency = models.FloatField(blank = True, null = True)
    proportion_of_group_heating = models.FloatField(blank = True, null = True)
    fuel_type_heating_system = models.CharField(blank = True, null = True)
    heating_system_1_make_model = models.CharField(blank = True, null = True)

    ###########HEATING SYSTEM #2####################
    efficiency_2 = models.FloatField(blank=True, null=True)
    proportion_of_group_heating_2 = models.FloatField(blank=True, null=True)
    fuel_type_heating_system_2 = models.CharField(blank=True, null=True)
    heating_system_1_make_model_2 = models.CharField(blank=True, null=True)

    ############CHP WASTE HEAT ########################
    group_heating_heat_from_chp = models.FloatField(blank=True, null=True, max_length=20)
    group_heating_power_station = models.BooleanField(default=False)
    group_heating_chp = models.BooleanField(default=False)
    ################CHP EFFFICIENCIES###############
    group_heating_electrical = models.BooleanField(default=False)
    group_heating_thermal = models.BooleanField(default=False)
    group_heating_fuel = models.CharField(blank=True, null=True, max_length=50)

    group_heating_any_other_comment = models.CharField(blank=True, null=True, max_length=50)


    #################PAGE 2####################################
    #############TOTAL FLOOR AREAS, HEAT LOSS FLOOR AREAS##########################
    ground_storey_heigh = models.FloatField(blank=True, null=True)
    ground_total_floor_area = models.FloatField(blank=True, null=True)
    ground_heatloss_floor_1 = models.FloatField(blank=True, null=True)
    ground_heatloss_floor_2 = models.FloatField(blank=True, null=True)
    ground_heatloss_floor_3 = models.FloatField(blank=True, null=True)
    ground_heatloss_floor_4 = models.FloatField(blank=True, null=True)
    ground_heatloss_perimeter = models.FloatField(blank=True, null=True)
    ground_heatloss_wall_1 = models.FloatField(blank=True, null=True)
    ground_heatloss_wall_2 = models.FloatField(blank=True, null=True)
    ground_heatloss_wall_3 = models.FloatField(blank=True, null=True)
    ground_heatloss_wall_4 = models.FloatField(blank=True, null=True)
    ground_heatloss_roof_1 = models.FloatField(blank=True, null=True)
    ground_heatloss_roof_2 = models.FloatField(blank=True, null=True)
    ground_heatloss_roof_3 = models.FloatField(blank=True, null=True)
    ground_heatloss_roof_4 = models.FloatField(blank=True, null=True)

    first_storey_heigh = models.FloatField(blank=True, null=True)
    first_total_floor_area = models.FloatField(blank=True, null=True)
    first_heatloss_floor_1 = models.FloatField(blank=True, null=True)
    first_heatloss_floor_2 = models.FloatField(blank=True, null=True)
    first_heatloss_floor_3 = models.FloatField(blank=True, null=True)
    first_heatloss_floor_4 = models.FloatField(blank=True, null=True)
    first_heatloss_perimeter = models.FloatField(blank=True, null=True)
    first_heatloss_wall_1 = models.FloatField(blank=True, null=True)
    first_heatloss_wall_2 = models.FloatField(blank=True, null=True)
    first_heatloss_wall_3 = models.FloatField(blank=True, null=True)
    first_heatloss_wall_4 = models.FloatField(blank=True, null=True)
    first_heatloss_roof_1 = models.FloatField(blank=True, null=True)
    first_heatloss_roof_2 = models.FloatField(blank=True, null=True)
    first_heatloss_roof_3 = models.FloatField(blank=True, null=True)
    first_heatloss_roof_4 = models.FloatField(blank=True, null=True)

    second_storey_heigh = models.FloatField(blank=True, null=True)
    second_total_floor_area = models.FloatField(blank=True, null=True)
    second_heatloss_floor_1 = models.FloatField(blank=True, null=True)
    second_heatloss_floor_2 = models.FloatField(blank=True, null=True)
    second_heatloss_floor_3 = models.FloatField(blank=True, null=True)
    second_heatloss_floor_4 = models.FloatField(blank=True, null=True)
    second_heatloss_perimeter = models.FloatField(blank=True, null=True)
    second_heatloss_wall_1 = models.FloatField(blank=True, null=True)
    second_heatloss_wall_2 = models.FloatField(blank=True, null=True)
    second_heatloss_wall_3 = models.FloatField(blank=True, null=True)
    second_heatloss_wall_4 = models.FloatField(blank=True, null=True)
    second_heatloss_roof_1 = models.FloatField(blank=True, null=True)
    second_heatloss_roof_2 = models.FloatField(blank=True, null=True)
    second_heatloss_roof_3 = models.FloatField(blank=True, null=True)
    second_heatloss_roof_4 = models.FloatField(blank=True, null=True)

    third_storey_heigh = models.FloatField(blank=True, null=True)
    third_total_floor_area = models.FloatField(blank=True, null=True)
    third_heatloss_floor_1 = models.FloatField(blank=True, null=True)
    third_heatloss_floor_2 = models.FloatField(blank=True, null=True)
    third_heatloss_floor_3 = models.FloatField(blank=True, null=True)
    third_heatloss_floor_4 = models.FloatField(blank=True, null=True)
    third_heatloss_perimeter = models.FloatField(blank=True, null=True)
    third_heatloss_wall_1 = models.FloatField(blank=True, null=True)
    third_heatloss_wall_2 = models.FloatField(blank=True, null=True)
    third_heatloss_wall_3 = models.FloatField(blank=True, null=True)
    third_heatloss_wall_4 = models.FloatField(blank=True, null=True)
    third_heatloss_roof_1 = models.FloatField(blank=True, null=True)
    third_heatloss_roof_2 = models.FloatField(blank=True, null=True)
    third_heatloss_roof_3 = models.FloatField(blank=True, null=True)
    third_heatloss_roof_4 = models.FloatField(blank=True, null=True)

    basement_storey_heigh = models.FloatField(blank=True, null=True)
    basement_total_floor_area = models.FloatField(blank=True, null=True)
    basement_heatloss_floor_1 = models.FloatField(blank=True, null=True)
    basement_heatloss_floor_2 = models.FloatField(blank=True, null=True)
    basement_heatloss_floor_3 = models.FloatField(blank=True, null=True)
    basement_heatloss_floor_4 = models.FloatField(blank=True, null=True)
    basement_heatloss_perimeter = models.FloatField(blank=True, null=True)
    basement_heatloss_wall_1 = models.FloatField(blank=True, null=True)
    basement_heatloss_wall_2 = models.FloatField(blank=True, null=True)
    basement_heatloss_wall_3 = models.FloatField(blank=True, null=True)
    basement_heatloss_wall_4 = models.FloatField(blank=True, null=True)
    basement_heatloss_roof_1 = models.FloatField(blank=True, null=True)
    basement_heatloss_roof_2 = models.FloatField(blank=True, null=True)
    basement_heatloss_roof_3 = models.FloatField(blank=True, null=True)
    basement_heatloss_roof_4 = models.FloatField(blank=True, null=True)

    ############

    living_area = models.FloatField(blank=True, null=True)
    room_in_roof_area = models.FloatField(blank=True, null=True)
    #########perimeter_total_ground_floor_(P/A)_ratio##################
    f_type_1 = models.FloatField(blank=True, null=True)
    f_type_2 = models.FloatField(blank=True, null=True)
    f_type_3 = models.FloatField(blank=True, null=True)

    draughts_tripping = models.FloatField(blank=True, null=True)
    lighting_design = models.CharField(blank=True, null=True, max_length=50)

    #########THERMAL MASS##################
    external_wall_light = models.BooleanField(default=False)
    external_wall_med = models.BooleanField(default=False)
    external_wall_heavy = models.BooleanField(default=False)

    floor_light = models.BooleanField(default=False)
    floor_med = models.BooleanField(default=False)
    floor_heavy = models.BooleanField(default=False)

    separating_wall_light = models.BooleanField(default=False)
    separating_wall_med = models.BooleanField(default=False)
    separating_wall_heavy = models.BooleanField(default=False)

    internal_wall_light = models.BooleanField(default=False)
    internal_wall_med = models.BooleanField(default=False)
    internal_wall_heavy = models.BooleanField(default=False)

    overall_thermall_mass = models.CharField(blank=True, null=True, max_length=50)

    room_1_opening = models.CharField(blank=True, null=True, max_length=20)
    room_1_opening_dimensions = models.FloatField(blank=True, null=True)
    room_1_glazing_details = models.CharField(blank=True, null=True, max_length=20)
    room_1_frame = models.CharField(blank=True, null=True, max_length=20)
    room_1_gap = models.CharField(blank=True, null=True, max_length=20)
    room_1_over_shading = models.CharField(blank=True, null=True, max_length=20)
    room_1_direction = models.CharField(blank=True, null=True, max_length=20)
    room_1_wall_roof_type = models.CharField(blank=True, null=True, max_length=20)
    room_1_openable_windows_doors = models.CharField(blank=True, null=True, max_length=20)
    room_1_windows_doors = models.CharField(blank=True, null=True, max_length=20)

    room_2_opening = models.CharField(blank=True, null=True, max_length=20)
    room_2_opening_dimensions = models.FloatField(blank=True, null=True)
    room_2_glazing_details = models.CharField(blank=True, null=True, max_length=20)
    room_2_frame = models.CharField(blank=True, null=True, max_length=20)
    room_2_gap = models.CharField(blank=True, null=True, max_length=20)
    room_2_over_shading = models.CharField(blank=True, null=True, max_length=20)
    room_2_direction = models.CharField(blank=True, null=True, max_length=20)
    room_2_wall_roof_type = models.CharField(blank=True, null=True, max_length=20)
    room_2_openable_windows_doors = models.CharField(blank=True, null=True, max_length=20)
    room_2_windows_doors = models.CharField(blank=True, null=True, max_length=20)

    room_3_opening = models.CharField(blank=True, null=True, max_length=20)
    room_3_opening_dimensions = models.FloatField(blank=True, null=True)
    room_3_glazing_details = models.CharField(blank=True, null=True, max_length=20)
    room_3_frame = models.CharField(blank=True, null=True, max_length=20)
    room_3_gap = models.CharField(blank=True, null=True, max_length=20)
    room_3_over_shading = models.CharField(blank=True, null=True, max_length=20)
    room_3_direction = models.CharField(blank=True, null=True, max_length=20)
    room_3_wall_roof_type = models.CharField(blank=True, null=True, max_length=20)
    room_3_openable_windows_doors = models.CharField(blank=True, null=True, max_length=20)
    room_3_windows_doors = models.CharField(blank=True, null=True, max_length=20)

    room_4_opening = models.CharField(blank=True, null=True, max_length=20)
    room_4_opening_dimensions = models.FloatField(blank=True, null=True)
    room_4_glazing_details = models.CharField(blank=True, null=True, max_length=20)
    room_4_frame = models.CharField(blank=True, null=True, max_length=20)
    room_4_gap = models.CharField(blank=True, null=True, max_length=20)
    room_4_over_shading = models.CharField(blank=True, null=True, max_length=20)
    room_4_direction = models.CharField(blank=True, null=True, max_length=20)
    room_4_wall_roof_type = models.CharField(blank=True, null=True, max_length=20)
    room_4_openable_windows_doors = models.CharField(blank=True, null=True, max_length=20)
    room_4_windows_doors = models.CharField(blank=True, null=True, max_length=20)

    room_5_opening = models.CharField(blank=True, null=True, max_length=20)
    room_5_opening_dimensions = models.FloatField(blank=True, null=True)
    room_5_glazing_details = models.CharField(blank=True, null=True, max_length=20)
    room_5_frame = models.CharField(blank=True, null=True, max_length=20)
    room_5_gap = models.CharField(blank=True, null=True, max_length=20)
    room_5_over_shading = models.CharField(blank=True, null=True, max_length=20)
    room_5_direction = models.CharField(blank=True, null=True, max_length=20)
    room_5_wall_roof_type = models.CharField(blank=True, null=True, max_length=20)
    room_5_openable_windows_doors = models.CharField(blank=True, null=True, max_length=20)
    room_5_windows_doors = models.CharField(blank=True, null=True, max_length=20)

    ###########ROOM DATA##########################

    room_1_chimney_flueless = models.FloatField(blank=True, null=True)
    room_1_open_flues = models.FloatField(blank=True, null=True)
    room_1_fans_vents = models.CharField(blank=True, null=True, max_length=20)
    room_1_rads_with_or_trvs = models.CharField(blank=True, null=True, max_length=20)
    room_1_number_of_fixed_lights = models.CharField(blank=True, null=True, max_length=20)
    room_1_type_of_fixed_light = models.CharField(blank=True, null=True, max_length=20)

    room_2_chimney_flueless = models.FloatField(blank=True, null=True)
    room_2_open_flues = models.FloatField(blank=True, null=True)
    room_2_fans_vents = models.CharField(blank=True, null=True, max_length=20)
    room_2_rads_with_or_trvs = models.CharField(blank=True, null=True, max_length=20)
    room_2_number_of_fixed_lights = models.CharField(blank=True, null=True, max_length=20)
    room_2_type_of_fixed_light = models.CharField(blank=True, null=True, max_length=20)

    room_3_chimney_flueless = models.FloatField(blank=True, null=True)
    room_3_open_flues = models.FloatField(blank=True, null=True)
    room_3_fans_vents = models.CharField(blank=True, null=True, max_length=20)
    room_3_rads_with_or_trvs = models.CharField(blank=True, null=True, max_length=20)
    room_3_number_of_fixed_lights = models.CharField(blank=True, null=True, max_length=20)
    room_3_type_of_fixed_light = models.CharField(blank=True, null=True, max_length=20)

    room_4_chimney_flueless = models.FloatField(blank=True, null=True)
    room_4_open_flues = models.FloatField(blank=True, null=True)
    room_4_fans_vents = models.CharField(blank=True, null=True, max_length=20)
    room_4_rads_with_or_trvs = models.CharField(blank=True, null=True, max_length=20)
    room_4_number_of_fixed_lights = models.CharField(blank=True, null=True, max_length=20)
    room_4_type_of_fixed_light = models.CharField(blank=True, null=True, max_length=20)

    room_5_chimney_flueless = models.FloatField(blank=True, null=True)
    room_5_open_flues = models.FloatField(blank=True, null=True)
    room_5_fans_vents = models.CharField(blank=True, null=True, max_length=20)
    room_5_rads_with_or_trvs = models.CharField(blank=True, null=True, max_length=20)
    room_5_number_of_fixed_lights = models.CharField(blank=True, null=True, max_length=20)
    room_5_type_of_fixed_light = models.CharField(blank=True, null=True, max_length=20)


    room_opening_total = models.CharField(blank=True, null=True, max_length=20)
    room_opening_dimensions_totaL = models.FloatField(blank=True, null=True)
    room_glazing_details_total = models.CharField(blank=True, null=True, max_length=20)
    room_frame_total = models.CharField(blank=True, null=True, max_length=20)
    room_gap_total = models.CharField(blank=True, null=True, max_length=20)
    room_over_shading_total = models.CharField(blank=True, null=True, max_length=20)
    room_direction_total = models.CharField(blank=True, null=True, max_length=20)
    room_wall_roof_type_total = models.CharField(blank=True, null=True, max_length=20)
    room_openable_windows_doors_total = models.CharField(blank=True, null=True, max_length=20)
    room_windows_doors_total = models.CharField(blank=True, null=True, max_length=20)

    room_chimney_flueless_total = models.FloatField(blank=True, null=True)
    room_open_flues_total = models.FloatField(blank=True, null=True)
    room_fans_vents_total = models.CharField(blank=True, null=True, max_length=20)
    room_rads_with_or_trvs_total = models.CharField(blank=True, null=True, max_length=20)
    room_number_of_fixed_lights_total = models.CharField(blank=True, null=True, max_length=20)
    room_type_of_fixed_light_total = models.CharField(blank=True, null=True, max_length=20)


    lidar = models.FileField(upload_to='lidar_assesment/', blank=True, null=True)

    class Meta:
        verbose_name = "Property Assessment"
        verbose_name_plural = "Property Assessments"


        ########################## NOT USED ############################################

class File(models.Model):
    FILE_TYPES = [
        ('document', 'Document'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('lidar', 'Lidar')
    ]

    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='uploads/%Y/%m/%d/')  # Store files in 'media/uploads/YYYY/MM/DD/'
    file_type = models.CharField(max_length=50, choices=FILE_TYPES)
    uploaded_at = models.DateTimeField(default=now)

    def __str__(self):
        return f"File {self.id} - {self.file.name}"