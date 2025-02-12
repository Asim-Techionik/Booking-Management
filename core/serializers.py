from rest_framework import serializers
from .models import UserModel, Job, Client, Accessor, Bid, Notification, Project, Quote, File, Assesment, Payment
from django.contrib.contenttypes.models import ContentType
import os



class UserModelSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    accessor_token = serializers.UUIDField(read_only=True)  # Make it read-only

    class Meta:
        model = UserModel
        fields = ['id', 'email', 'first_name', 'last_name', 'phone_number', 'password', 'user_type', 'accessor_token', 'preference', 'is_staff', 'is_superuser', 'date_joined']
        read_only_fields = ['id', 'date_joined']

    def validate(self, attrs):
        if 'user_type' in attrs and attrs.get('user_type') not in ['client', 'accessor', 'admin']:
            raise serializers.ValidationError({"user_type": "Invalid user type. Must be 'client' or 'accessor'."})

        if attrs.get('is_staff') and attrs.get('user_type') != 'admin':
            raise serializers.ValidationError({"is_staff": "Only 'admin' can be an admin."})

        if attrs.get('is_superuser') and attrs.get('user_type') != 'admin':
            raise serializers.ValidationError({"is_superuser": "Only 'admin' can be a superuser."})
        return attrs

    def create(self, validated_data):
        user = UserModel.objects.create_user(**validated_data)
        return user

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ['id', 'first_name', 'last_name', 'email', 'phone_number']

class AccessorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Accessor
        fields = ['id', 'first_name', 'last_name', 'email', 'phone_number']

class JobSerializer(serializers.ModelSerializer):
    client_id = serializers.PrimaryKeyRelatedField(queryset=Client.objects.all(), source='client', write_only=True)

    class Meta:
        model = Job
        fields = [
            'id',
            'building_type',
            'client',
            'status',
            'preferred_date',
            'preferred_time',
            'property_type',
            'property_size',
            'bedrooms',
            'additional_features',
            'heat_pump_installed',
            'nearest_town',
            'county',
            'ber_purpose',
            'created_at',
            'updated_at',
            'name',
            'email_address',  # Add this to allow input of client_id
            'mobile_number',
            'client_id'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'client']

class TableJob(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ['id', 'building_type', 'property_size', 'bedrooms',
                  'heat_pump_installed', 'ber_purpose', 'preferred_date',
                  'status', 'county', 'created_at']

class BidSerializer(serializers.ModelSerializer):
    assessor = serializers.PrimaryKeyRelatedField(queryset=Accessor.objects.all())  # Assessor should be linked to the Accessor model
    job = serializers.PrimaryKeyRelatedField(queryset=Job.objects.all())  # Job should be linked to the Job model
    class Meta:
        model = Bid
        fields = [
            'id',
            'amount',
            'availability',
            'assessor',
            'job',
            'created_at',
            'insurance',
            'SEAI_Registered',
            'VAT_Registered',

        ]
        read_only_fields = ['id', 'created_at']  # id and created_at are auto-generated

    def validate(self, attrs):
        # Additional validation can be added here if needed
        return attrs


class NotificationSerializer(serializers.ModelSerializer):
    sender = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ['id', 'message', 'notification_type', 'sender', 'status', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_sender(self, obj):
        """
        Get the sender based on the GenericForeignKey.
        We check the ContentType of the sender and return the appropriate model (Client or Accessor).
        """
        # Get the correct model instance based on the content type and object ID
        sender_obj = obj.sender  # This will either be a Client or an Accessor

        if isinstance(sender_obj, Client):
            return {
                'id': sender_obj.id,
                'first_name': sender_obj.first_name,
                'last_name': sender_obj.last_name,
                'email': sender_obj.email,
            }
        elif isinstance(sender_obj, Accessor):
            return {
                'id': sender_obj.id,
                'first_name': sender_obj.first_name,
                'last_name': sender_obj.last_name,
                'email': sender_obj.email,
            }

        return None


class ProjectSerializer(serializers.ModelSerializer):
    # Nested representations for related fields
    client_email = serializers.ReadOnlyField(source='client.user.email')
    accessor_email = serializers.ReadOnlyField(source='accessor.user.email')

    class Meta:
        model = Project
        fields = [
            'id',
            'job',
            'client',
            'client_email',
            'accessor',
            'accessor_email',
            'status',
            'start_date',
            'end_date',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at', 'job', 'client', 'accessor']

    def update(self, instance, validated_data):
        # Custom update logic if needed
        return super().update(instance, validated_data)


# def validate_lidar_file(value):
#     # Check the file extension
#     valid_extensions = ['.las', '.laz']
#     extension = os.path.splitext(value.name)[1].lower()
#
#     if extension not in valid_extensions:
#         raise serializers.ValidationError("LIDAR file must be in LAS or LAZ format.")
#
#     return value


class QuoteSerializer(serializers.ModelSerializer):
    assessments = serializers.SerializerMethodField()
    class Meta:
        model = Quote
        fields = '__all__'

    def get_assessments(self, obj):

        return obj.assessments.values_list('id', flat=True)

class AssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assesment
        fields = '__all__'


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'id',
            'assessor',
            'job',
            'bid',
            'amount',
            'currency',
            'stripe_payment_id',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'amount']  # Amount is set by the save method

    def validate(self, attrs):
        # Additional validation can be added here if needed
        return attrs

class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ['id', 'project', 'file', 'file_type', 'uploaded_at']

    # Remove queryset and read_only argument for project field
    project = serializers.PrimaryKeyRelatedField(queryset=Project.objects.all(), required=False)




