from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .models import UserModel, Job, Client, Accessor, Notification, Bid, Project, File, Quote, Assesment, Payment
from .serializers import UserModelSerializer, JobSerializer, BidSerializer, NotificationSerializer, QuoteSerializer, FileSerializer, ProjectSerializer, ClientSerializer, AccessorSerializer, TableJob, AssessmentSerializer, PaymentSerializer
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import RetrieveAPIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotAuthenticated
from django.contrib.contenttypes.models import ContentType
from rest_framework.exceptions import PermissionDenied
from django.utils import timezone
from django.utils.timezone import now
from rest_framework.authentication import TokenAuthentication
import logging
from django.db.models import Count, Q
from django.conf import settings
import stripe
from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from django.http import HttpResponse
from core.email_backend import send_gmail_api
from django.contrib.auth.hashers import make_password
import random
from datetime import timedelta
import uuid








stripe.api_key = settings.STRIPE_TEST_SECRET_KEY


logger = logging.getLogger(__name__)

       ################ BOOKING PAGE #######################

class GetQuoteView(APIView):
    authentication_classes = []
    def get(self, request):
        """
        Handle GET request to create a new GetQuote instance with an auto-generated ID.
        """
        quote = Quote.objects.create()
        assessment = Assesment.objects.create(
            quote=quote,  # Use the primary key of the created Quote as a foreign key
        )

        # Serialize the Quote data along with the Assessment ID
        quote_serializer = QuoteSerializer(quote)
        response_data = {
            "quote": quote_serializer.data,
            "assessment_id": assessment.id,
        }

        return Response(response_data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(request_body=QuoteSerializer)
    # def put(self, request, pk):
    #     """
    #     Handle PUT request to update an existing GetQuote instance.
    #     """
    #     # Fetch the existing Quote instance by its primary key
    #     quote = get_object_or_404(Quote, pk=pk)
    #
    #     # Pass the updated data from request.data to the serializer
    #     serializer = QuoteSerializer(quote, data=request.data, partial=True)
    #
    #     if serializer.is_valid():
    #         # Save the updated Quote instance
    #         serializer.save()
    #
    #         return Response(serializer.data, status=status.HTTP_200_OK)
    #
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def put(self, request, pk):
        """
        Update the Quote instance and create a user and job if all attributes except lidar are provided.
        """
        quote = get_object_or_404(Quote, pk=pk)

        serializer = QuoteSerializer(quote, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()

            # Check if all required attributes except lidar are filled
            required_fields = [
                'name', 'email_address', 'mobile_number',
                'building_type', 'preferred_date', 'preferred_time',
                'property_type', 'property_size', 'bedrooms',
                'heat_pump_installed', 'county', 'nearest_town', 'ber_purpose'
            ]

            if all(getattr(quote, field) for field in required_fields):
                # Update or create UserModel with user_type explicitly set to 'client'
                email = quote.email_address
                user, created = UserModel.objects.get_or_create(
                    email=email,
                    defaults={
                        "first_name": quote.name.split()[0] if quote.name else "",
                        "last_name": quote.name.split()[1] if quote.name and len(quote.name.split()) > 1 else "",
                        "phone_number": quote.mobile_number,
                        "password": str(uuid.uuid4())[:8],
                        "user_type": "client"  # Ensure user_type is client
                    }
                )

                # Ensure the Client instance exists and is linked to the user
                client, client_created = Client.objects.get_or_create(
                    user=user,
                    defaults={
                        "email": email,
                        "phone_number": quote.mobile_number,
                        "first_name": user.first_name,
                        "last_name": user.last_name
                    }
                )

                # Update or create Job linked to the correct Client
                job, job_created = Job.objects.update_or_create(
                    client=client,
                    defaults={
                        "building_type": quote.building_type,
                        "preferred_date": quote.preferred_date,
                        "preferred_time": quote.preferred_time,
                        "property_type": quote.property_type,
                        "property_size": quote.property_size,
                        "bedrooms": quote.bedrooms,
                        "additional_features": quote.additional_features,
                        "heat_pump_installed": quote.heat_pump_installed,
                        "county": quote.county,
                        "nearest_town": quote.nearest_town,
                        "ber_purpose": quote.ber_purpose,
                        "name": quote.name,
                        "email_address": quote.email_address,
                        "mobile_number": quote.mobile_number,
                        "status": "pending"
                    }
                )

            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserCreateAPIView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(request_body=UserModelSerializer)
    def post(self, request, *args, **kwargs):
        serializer = UserModelSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginAPIView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(request_body=UserModelSerializer)
    def post(self, request, *args, **kwargs):
        """
        Authenticate user and return JWT tokens (access and refresh).
        """
        email = request.data.get('email')
        phone_number = request.data.get('phone_number')
        password = request.data.get('password')

        # Ensure that both email and phone number are provided for 'client' users
        if not email or (UserModel.objects.filter(email=email).exists() and
                         UserModel.objects.get(email=email).user_type == 'client' and not phone_number):
            return Response({"detail": "For client users, both email and phone number are required."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Authenticate client users without checking the password
        if UserModel.objects.filter(email=email, phone_number=phone_number).exists():
            user = UserModel.objects.get(email=email, phone_number=phone_number)
            if user.user_type == 'client':
                # No password check for client users
                refresh = RefreshToken.for_user(user)
                access_token = refresh.access_token

                # Return both tokens for client user
                return Response({
                    'refresh': str(refresh),
                    'access': str(access_token),
                    'user_type': user.user_type,
                }, status=status.HTTP_200_OK)

        # If it's not a client or the combination of email and phone number doesn't match, attempt regular authentication
        user = authenticate(request, username=email, password=password)

        if user is None:
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        # If authentication is successful, create JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token

        # Return both tokens
        return Response({
            'refresh': str(refresh),
            'access': str(access_token),
            'user_type': user.user_type,
        }, status=status.HTTP_200_OK)



# class UserLoginAPIView(APIView):
#     permission_classes = [AllowAny]
#
#     @swagger_auto_schema(request_body=UserModelSerializer)
#     def post(self, request, *args, **kwargs):
#         """
#         Authenticate user and return JWT tokens (access and refresh).
#         """
#         email = request.data.get('email')
#         phone_number = request.data.get('phone_number')
#         password = request.data.get('password')
#
#         # Ensure that both email and phone number are provided for 'client' users
#         if not email or (UserModel.objects.filter(email=email).exists() and UserModel.objects.get(email=email).user_type == 'client' and not phone_number):
#             return Response({"detail": "For client users, both email and phone number are required."},
#                             status=status.HTTP_400_BAD_REQUEST)
#
#         # Authenticate client users without checking the password
#         if UserModel.objects.filter(email=email, phone_number=phone_number).exists():
#             user = UserModel.objects.get(email=email, phone_number=phone_number)
#             if user.user_type == 'client':
#                 # No password check for client users
#                 refresh = RefreshToken.for_user(user)
#                 access_token = refresh.access_token
#
#                 # Return both tokens for client user
#                 return Response({
#                     'refresh': str(refresh),
#                     'access': str(access_token),
#                     'user_type': user.user_type,
#                 }, status=status.HTTP_200_OK)
#
#         # If it's not a client or the combination of email and phone number doesn't match, attempt regular authentication
#         user = authenticate(request, email=email, password=password)
#
#         if user is None:
#             return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
#
#         # Check is_active status only for 'accessor' users
#         if user.user_type == 'accessor' and not user.is_active:
#             return Response({"detail": "Account is not activated. Please activate your account first."}, status=status.HTTP_403_FORBIDDEN)
#
#         # If authentication is successful, create JWT tokens
#         refresh = RefreshToken.for_user(user)
#         access_token = refresh.access_token
#
#         # Return both tokens
#         return Response({
#             'refresh': str(refresh),
#             'access': str(access_token),
#             'user_type': user.user_type,
#         }, status=status.HTTP_200_OK)


class UpdateUserView(APIView):
    permission_classes = [IsAuthenticated]

    # @swagger_auto_schema(request_body=UserModelSerializer)
    def put(self, request):
        user = request.user

        # Check if the authenticated user is of type 'client'
        if user.user_type != 'accessor':
            return Response({"error": "Only accessors are allowed to update their information."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = UserModelSerializer(user, data=request.data, partial=True)  # Allow partial updates
        if serializer.is_valid():
            user = serializer.save()
            return Response(UserModelSerializer(user).data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]  # Only authenticated users can view their notifications

    def get(self, request):
        user = request.user

        # Check if the user is an Accessor or Client
        try:
            accessor = Accessor.objects.get(user=user)
            notifications = Notification.objects.filter(recipient=user).order_by('-created_at')
        except Accessor.DoesNotExist:
            try:
                client = Client.objects.get(user=user)
                notifications = Notification.objects.filter(recipient=user).order_by('-created_at')
            except Client.DoesNotExist:
                return Response({"error": "User is not a client or accessor."},
                                status=status.HTTP_400_BAD_REQUEST)

        # Serialize the notifications
        serializer = NotificationSerializer(notifications, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

class MarkNotificationAsReadView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access

    @swagger_auto_schema(request_body=NotificationSerializer)
    def post(self, request, notification_id):
        user = request.user

        # Find the notification by ID
        try:
            notification = Notification.objects.get(id=notification_id, recipient=user)
        except Notification.DoesNotExist:
            return Response({"error": "Notification not found or you're not authorized to mark it."},
                            status=status.HTTP_404_NOT_FOUND)

        # Update the status of the notification to 'read'
        notification.status = 'read'
        notification.save()

        return Response({"message": "Notification marked as read."}, status=status.HTTP_200_OK)



        ############## HOMEOWNER VIEWS ###################         #

class ClientJobListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        List all jobs created by the authenticated client.
        """
        # Ensure the user has an associated Client
        try:
            client = request.user.client
        except Client.DoesNotExist:
            return Response({"error": "You do not have any associated jobs."}, status=status.HTTP_400_BAD_REQUEST)

        # Filter jobs created by the client
        jobs = Job.objects.filter(client=client)
        serializer = JobSerializer(jobs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=JobSerializer)
    def patch(self, request, pk):
        """
        Update the status of a specific job for the authenticated client.
        """
        try:
            client = request.user.client
        except Client.DoesNotExist:
            return Response({"error": "You do not have any associated jobs."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            job = Job.objects.get(pk=pk, client=client)
        except Job.DoesNotExist:
            return Response({"error": "Job not found or you do not have permission to update this job."}, status=status.HTTP_404_NOT_FOUND)

        job_status = request.data.get('status')  # Renamed to avoid conflict with model field
        if job_status:
            job.status = job_status
            job.save()
            return Response(JobSerializer(job).data, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Status is required."}, status=status.HTTP_400_BAD_REQUEST)

class ClientJobCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Generate a new ID for a job (primary key in the database) and return it in the response.
        """
        try:
            # Create a new Job instance and generate a unique ID
            job = Job.objects.create(client=request.user.client)
            return Response({"job_id": job.id}, status=status.HTTP_201_CREATED)
        except Client.DoesNotExist:
            return Response({"error": "Client does not exist for the authenticated user."}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(request_body=JobSerializer)
    def put(self, request, job_id):
        """
        Update the attributes of an existing job for the authenticated client using the job_id in the URL.
        """
        try:
            client = request.user.client
        except Client.DoesNotExist:
            return Response({"error": "Client does not exist for the authenticated user."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            job = Job.objects.get(id=job_id, client=client)
        except Job.DoesNotExist:
            return Response({"error": "Job does not exist or does not belong to the authenticated client."}, status=status.HTTP_404_NOT_FOUND)

        serializer = JobSerializer(job, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class JobSearchView(APIView):
    """
    View to search for jobs based on query parameters.
    """

    def get(self, request):
        # Retrieve query parameters
        property_type = request.query_params.get('property_type')
        property_size = request.query_params.get('property_size')
        bedrooms = request.query_params.get('bedrooms')
        county = request.query_params.get('county')
        nearest_town = request.query_params.get('nearest_town')

        # Build queryset dynamically based on provided parameters
        queryset = Job.objects.all()
        if property_type:
            queryset = queryset.filter(property_type__icontains=property_type)
        if property_size:
            queryset = queryset.filter(property_size__icontains=property_size)
        if bedrooms:
            queryset = queryset.filter(bedrooms__icontains=bedrooms)
        if county:
            queryset = queryset.filter(location__icontains=county)
        if nearest_town:
            queryset = queryset.filter(nearest_town__icontains=nearest_town)

        # Serialize the filtered queryset
        serializer = JobSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class JobsAndBidsView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure only authenticated clients can access

    def get(self, request):
        user = request.user

        try:
            # Retrieve the client associated with the authenticated user
            client = Client.objects.get(user=user)
        except Client.DoesNotExist:
            return Response({"error": "User is not a client."}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve all the jobs posted by the client that have at least one bid
        jobs_with_bids = Job.objects.filter(client=client).filter(bids__isnull=False).distinct()

        job_details = []
        for job in jobs_with_bids:
            # For each job, retrieve all bids associated with it
            bids = Bid.objects.filter(job=job)

            bid_details = []
            for bid in bids:
                bid_details.append({
                    "id": bid.id,
                    "amount": bid.amount,
                    "availability": bid.availability,
                    "insurance": bid.insurance,
                    "SEAI_Registered": bid.SEAI_Registered,
                    "VAT_Registered": bid.VAT_Registered,
                    "assessor": {
                        "id": bid.assessor.id,
                        "first_name": bid.assessor.first_name,
                        "last_name": bid.assessor.last_name,
                        "email": bid.assessor.user.email
                    },
                    "created_at": bid.created_at,
                })

            job_details.append({
                "id": job.id,
                "bedrooms": job.bedrooms,
                "building_type": job.building_type,
                "nearest_town": job.nearest_town,
                "status": job.status,
                "created_at": job.created_at,
                "client": {
                    "id": client.id,
                    "first_name": client.first_name,
                    "last_name": client.last_name,
                    "email": client.user.email
                },
                "bids": bid_details
            })

        return Response(job_details, status=status.HTTP_200_OK)


class BidDetailView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access

    def get(self, request, bid_id):
        user = request.user

        try:
            # Retrieve the bid with the given bid_id
            bid = Bid.objects.get(id=bid_id)
        except Bid.DoesNotExist:
            return Response({"error": "Bid not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if the user is either the client who posted the job or the assessor who made the bid
        if bid.job.client.user != user and bid.assessor.user != user:
            return Response({"error": "You are not authorized to view this bid."}, status=status.HTTP_403_FORBIDDEN)

        # Serialize and return only the bid details
        bid_data = {
            "id": bid.id,
            "amount": bid.amount,
            "availability": bid.availability,
            "insurance": bid.insurance,
            "SEAI_Registered": bid.SEAI_Registered,
            "VAT_Registered": bid.VAT_Registered,
            "assessor": {
                "id": bid.assessor.id,
                "first_name": bid.assessor.first_name,
                "last_name": bid.assessor.last_name,
                "email": bid.assessor.user.email
            },
            "created_at": bid.created_at
        }

        return Response(bid_data, status=status.HTTP_200_OK)

    # @swagger_auto_schema(request_body=BidSerializer)
    def put(self, request, bid_id):
        user = request.user

        try:
            # Retrieve the bid with the given bid_id
            bid = Bid.objects.get(id=bid_id)
        except Bid.DoesNotExist:
            return Response({"error": "Bid not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if the user is either the client who posted the job or the assessor who made the bid
        if bid.job.client.user != user and bid.assessor.user != user:
            return Response({"error": "You are not authorized to update this bid."}, status=status.HTTP_403_FORBIDDEN)

        # Ensure only the assessor or client can update the bid. You may want to restrict which fields can be updated.
        # Create a serializer for updating the bid. Use partial=True to allow partial updates.
        serializer = BidSerializer(bid, data=request.data, partial=True)

        if serializer.is_valid():
            updated_bid = serializer.save()

            # Optionally, create notifications or perform other actions after the bid is updated.
            # If the bid amount has changed, create a notification for the client
            if 'amount' in request.data and request.data['amount'] != str(bid.amount):
                notification = Notification.objects.create(
                    message=f"A new bid of {updated_bid.amount} has been placed for your job by {updated_bid.assessor.user.first_name} {updated_bid.assessor.user.last_name}.",
                    notification_type='bid',
                    sender=updated_bid.assessor.user,
                    recipient=updated_bid.job.client.user,  # Assign the user (UserModel) of the client here
                )

            # Optionally, create notifications or perform other actions after the bid is updated.
            # Serialize and return the updated bid details
            bid_data = {
                "id": updated_bid.id,
                "amount": updated_bid.amount,
                "availability": updated_bid.availability,
                "insurance": updated_bid.insurance,
                "SEAI_Registered": updated_bid.SEAI_Registered,
                "VAT_Registered": updated_bid.VAT_Registered,
                "assessor": {
                    "id": updated_bid.assessor.id,
                    "first_name": updated_bid.assessor.first_name,
                    "last_name": updated_bid.assessor.last_name,
                    "email": updated_bid.assessor.user.email
                },
                "created_at": updated_bid.created_at
            }

            return Response(bid_data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AcceptBidView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=BidSerializer)
    def post(self, request, bid_id=None):
        user = request.user

        try:
            # Get the client object that is associated with the authenticated user
            client = Client.objects.get(user=user)
        except Client.DoesNotExist:
            return Response({"error": "User is not a client."}, status=status.HTTP_400_BAD_REQUEST)
        client = Client.objects.get(user=user)


        try:
            bid = Bid.objects.get(id=bid_id)
            job = bid.job

            if job.client != client:
                return Response({"error": "You are not the client who posted this job."}, status=status.HTTP_400_BAD_REQUEST)

            # Accept the bid and change the job status to 'Completed'
            job.status = 'In Progress'
            job.save()

            # Create the project
            project = Project.objects.create(
                job=job,
                client=client,
                accessor=bid.assessor,
                status='In Progress',
                start_date=now(),
            )

            # Automatically create the assessment linked to the project
            assessment = Assesment.objects.create(
                 project=project,
                 accessor=bid.assessor,
                 client=client,
             )

            sender_content_type = ContentType.objects.get_for_model(client)
            notification = Notification.objects.create(
                message=f"Your bid of {bid.amount} for job  has been accepted by {client.user.first_name} {client.user.last_name}.",
                notification_type='bid_accepted',
                sender_content_type=sender_content_type,
                sender_object_id=client.id,
                recipient=bid.assessor.user,  # The assessor will be the recipient
            )

            # Find all users that are admin
            Usermodel = UserModel.objects.filter(is_staff=True)

            # Send notification to all admins
            for admin in Usermodel:
                Notification.objects.create(
                    message=f"Home Owner {client.user.first_name} {client.user.last_name} has accepted a bid for the job by Accessor {bid.assessor.user.first_name} {bid.assessor.user.last_name}.",
                    notification_type='admin_bid_accepted',
                    sender_content_type=sender_content_type,
                    sender_object_id=client.id,  # Client is the sender
                    recipient=admin,  # Admin is the recipient
                )

            return Response({
                "message": "Bid accepted successfully. A project and assessment have been created.",
                "project_id": project.id,
                "assessment_id": assessment.id,
            }, status=status.HTTP_200_OK)

        except Bid.DoesNotExist:
            return Response({"error": "Bid not found."}, status=status.HTTP_404_NOT_FOUND)


class CreateCheckoutSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, bid_id=None, *args, **kwargs):
        try:
            # Get the Bid object from the bid_id in the URL
            bid = Bid.objects.get(id=bid_id)

            # Get the details of the payment associated with the bid
            payment_details = {
                'bid_id': bid.id,
                'job': bid.job.building_type,
                'assessor': bid.assessor.user.email,
                'amount': bid.amount,  # Bid amount in dollars
                'availability': bid.availability,
                'insurance': bid.insurance,
                'SEAI_Registered': bid.SEAI_Registered,
                'VAT_Registered': bid.VAT_Registered,
            }

            # Return the payment details
            return Response(payment_details)

        except Bid.DoesNotExist:
            return Response({'error': 'Bid not found.'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=400)

    def post(self, request, bid_id=None, *args, **kwargs):

        try:
            # Get the Bid object from the bid_id in the URL
            bid = Bid.objects.get(id=bid_id)

            # Create a Stripe checkout session with required URLs
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {
                                'name': f"Bid for Job {bid.job.building_type}",
                            },
                            'unit_amount': int(bid.amount * 100),  # Stripe expects amount in cents
                        },
                        'quantity': 1,
                    },
                ],
                mode='payment',
                success_url='https://example.com/success',  # Placeholder success URL
                cancel_url='https://example.com/cancel',  # Placeholder cancel URL
            )

            # Create the Payment record in the database after the session is created
            payment = Payment.objects.create(
                assessor=bid.assessor,
                job=bid.job,
                bid=bid,
                amount=bid.amount,  # Use the bid amount
                currency='usd',  # Assuming USD
                stripe_payment_id=checkout_session.id,  # Use the session ID
            )

            # Return status 201 Created with payment and checkout session details
            return Response({
                'status': 'Payment session created successfully',
                'payment_id': payment.id,
                'checkout_session_id': checkout_session.id
            }, status=201)

        except Bid.DoesNotExist:
            return Response({'error': 'Bid not found.'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=400)

###################### ################# ################## ####################### #########################


                         ########## ACCESSORS SCREEN ##################
class AccessorJobView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Check if the authenticated user is an Accessor
        user = request.user
        if user.user_type != 'accessor':
            return Response({"error": "You do not have permission to access this endpoint."},
                            status=status.HTTP_403_FORBIDDEN)

        # Get the preference set by the user
        preference = user.preference
        if not preference:
            return Response({"error": "User preference is not set."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Filter jobs based on the user's preference and 'pending' status
        jobs = Job.objects.filter(status='pending', county__iexact=preference)  # Case-insensitive match

        # Serialize the filtered jobs and quotes
        job_serializer = JobSerializer(jobs, many=True)

        # Combine the serialized data into one response
        response_data = {
            "pending_jobs": job_serializer.data,
        }

        return Response(response_data, status=status.HTTP_200_OK)



class BidCreateView(APIView):

    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can create a bid

    @swagger_auto_schema(request_body=BidSerializer)

    def post(self, request, job_id=None):
        user = request.user

        try:
            accessor = Accessor.objects.get(user=user)
        except Accessor.DoesNotExist:
            return Response({"error": "User is not an accessor."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            job = Job.objects.get(id=job_id)
            if job.status != 'pending':
                return Response({"error": "Bids can only be placed on jobs with 'Pending' status."},
                                 status=status.HTTP_400_BAD_REQUEST)
        except Job.DoesNotExist:
            return Response({"error": "Job not found."}, status=status.HTTP_404_NOT_FOUND)

        data = request.data.copy()
        data['assessor'] = accessor.id
        data['job'] = job.id

        serializer = BidSerializer(data=data)
        if serializer.is_valid():
            bid = serializer.save()

            # Create a notification for the client about the new bid
            notification = Notification.objects.create(
                message=f"A new bid of {bid.amount} has been placed for your job by {accessor.user.first_name} {accessor.user.last_name}.",
                notification_type='bid',
                sender=accessor,
                recipient=job.client.user,  # Assign the user (UserModel) of the client here
            )

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class MyBidsView(APIView):
    permission_classes = [IsAuthenticated]  # Only authenticated users can access the view
    def get(self, request):
        # Retrieve the accessor instance from the logged-in user
        accessor = request.user.accessor

        # Fetch all bids placed by the accessor
        bids = Bid.objects.filter(assessor=accessor)

        bid_data = []

        # Iterate over all the bids and construct the response
        for bid in bids:
            # Find the lowest bid for the job
            lowest_bid = Bid.objects.filter(job=bid.job).order_by('amount').first()

            # Append the required data for the response
            bid_data.append({
                "bid_id": bid.id,  # Include the bid ID
                "amount": bid.amount,
                "availability": bid.availability,  # Include bid availability
                "job": {
                    "job_id": bid.job.id,
                    "status": bid.job.status,  # Ensure "job.status" exists
                    "nearest_town": bid.job.nearest_town,
                    "county": bid.job.county,
                    "property_type": bid.job.property_type,
                    "property_size": bid.job.property_size,
                    "bedrooms": bid.job.bedrooms,
                    "heat_pump_installed": bid.job.heat_pump_installed,
                    "ber_purpose": bid.job.ber_purpose,
                    "additional_features": bid.job.additional_features,
                    "preferred_date": bid.job.preferred_date,
                    "client_id": bid.job.client_id,
                    "lowest_bid": {
                        "bid_id": lowest_bid.id if lowest_bid else None,
                        "amount": lowest_bid.amount if lowest_bid else None,
                    }
                },
            })

        return Response(bid_data, status=status.HTTP_200_OK)

class ListAccessorBidsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        try:
            # Get the accessor object associated with the authenticated user
            accessor = Accessor.objects.get(user=user)
        except Accessor.DoesNotExist:
            return Response({"error": "User is not an accessor."}, status=status.HTTP_400_BAD_REQUEST)

        # Get all bids placed by the accessor
        bids = Bid.objects.filter(assessor=accessor).select_related('job')

        # Serialize the data, including related job details
        bid_data = []
        for bid in bids:
            bid_data.append({
                "bid_id": bid.id,
                "amount": bid.amount,
                # Remove or replace "status" if it doesn't exist on the Bid model
                # "status": bid.status,  # Comment or remove this line if invalid
                "job": {
                    "job_id": bid.job.id,
                    "status": bid.job.status,  # Ensure "job.status" exists
                    "nearest_town": bid.job.nearest_town,
                    "county": bid.job.county,
                    "property_type": bid.job.property_type,
                    "client": {
                        "client_id": bid.job.client.id,
                        "name": f"{bid.job.client.user.first_name} {bid.job.client.user.last_name}",
                        "eamil": f"{bid.job.client.user.email}",
                        "phone_number": f"{bid.job.client.user.phone_number}"
                    },
                },
            })

        return Response({"bids": bid_data}, status=status.HTTP_200_OK)



class ProjectListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        try:
            # Ensure the user is an accessor
            accessor = Accessor.objects.get(user=user)
        except Accessor.DoesNotExist:
            return Response({"error": "You are not an Accessor."}, status=status.HTTP_403_FORBIDDEN)

        # Get all projects related to the accessor (i.e., where the accessor is assigned)
        projects = Project.objects.filter(accessor=accessor)


        # Prepare project data along with assessment IDs
        project_data = []
        for project in projects:
            # Fetch the job associated with the project
            job = project.job  # Assuming `job` is the foreign key in the `Project` model

            # Serialize the job details
            job_details = {
                "id": job.id,
                "created_at": job.created_at,
                "nearest_town": job.nearest_town,
                "county": job.county,
                "bedrooms": job.bedrooms,
                "heat_pump_installed": job.heat_pump_installed,
                "building_type": job.building_type,
                "additional_features": job.additional_features,
                "purpose": "job.purpose",
                "status": job.status,
                "preferred_date": job.preferred_date,
                "property_type": job.property_type,
                "property_size": job.property_size,
            } if job else None

            # Retrieve associated assessments for each project
            assessments = Assesment.objects.filter(project=project)

            # Add assessment IDs to project data
            assessment_ids = assessments.values_list('id', flat=True)

            # Serialize project and append the assessment IDs
            project_info = ProjectSerializer(project).data
            project_info['assessment_ids'] = list(assessment_ids)
            project_info['job_details'] = job_details  # Include serialized job details
            project_data.append(project_info)

        return Response(project_data, status=status.HTTP_200_OK)


class ProjectDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=ProjectSerializer)
    def put(self, request, project_id):
        user = request.user
        project = get_object_or_404(Project, id=project_id)

        if project.client.user == user:
            serializer = ProjectSerializer(project, data=request.data, partial=True)
        elif project.accessor.user == user:
            serializer = ProjectSerializer(project, data=request.data, partial=True)
        else:
            return Response({"error": "You do not have access to this project."}, status=status.HTTP_403_FORBIDDEN)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, project_id):
        user = request.user
        project = get_object_or_404(Project, id=project_id)

        # Ensure the user is either the client or accessor for the project
        if project.client.user == user:
            # Client can see the accessor's details
            accessor_details = {
                "first_name": project.accessor.user.first_name,
                "last_name": project.accessor.user.last_name,
                "phone_number": project.accessor.user.phone_number,
                "email": project.accessor.user.email,
            }
            project_data = ProjectSerializer(project).data
            project_data['accessor_details'] = accessor_details
        elif project.accessor.user == user:
            # Accessor can see the client's details
            client_details = {
                "first_name": project.client.user.first_name,
                "last_name": project.client.user.last_name,
                "phone_number": project.client.user.phone_number,
                "email": project.client.user.email,
            }
            project_data = ProjectSerializer(project).data
            project_data['client_details'] = client_details
        else:
            return Response({"error": "You do not have access to this project."}, status=status.HTTP_403_FORBIDDEN)

        return Response(project_data, status=status.HTTP_200_OK)

class AssessmentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Ensure the user is an accessor
        try:
            accessor = Accessor.objects.get(user=request.user)
        except Accessor.DoesNotExist:
            return Response(
                {"error": "You are not authorized to access this endpoint."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Retrieve the first project associated with the accessor
        project = Project.objects.filter(client=accessor.client).first()  # Or customize this query as needed
        if not project:
            return Response(
                {"error": "No project associated with your client."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create a new Assessment object
        assessment = Assesment.objects.create(
            accessor=accessor,
            project=project,
            client=accessor.client,  # You could also link this based on specific criteria
        )

        return Response({"assessment_id": assessment.id}, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(request_body=AssessmentSerializer)
    def put(self, request, assessment_id):
        # Ensure the user is an accessor
        try:
            accessor = Accessor.objects.get(user=request.user)
        except Accessor.DoesNotExist:
            return Response({"error": "You are not authorized to access this endpoint."},
                            status=status.HTTP_403_FORBIDDEN)

        try:
            # Retrieve the Assessment object
            assessment = Assesment.objects.get(id=assessment_id, accessor=accessor)
        except Assesment.DoesNotExist:
            return Response({"error": "Assessment not found or you do not have permission to update it."},
                            status=status.HTTP_404_NOT_FOUND)

        # Update the Assessment with provided data
        serializer = AssessmentSerializer(assessment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AssessmentQuoteView(APIView):
    permission_classes = [IsAuthenticated] # Ensure the user is authenticated via Bearer token

    @swagger_auto_schema(request_body=AssessmentSerializer)
    def put(self, request, assessment_id):
        # Extract accessor_id from the authenticated user
        user = request.user
        try:
            accessor = Accessor.objects.get(user=user)
        except Accessor.DoesNotExist:
            return Response({"error": "Accessor not found."}, status=status.HTTP_404_NOT_FOUND)

        # Fetch the assessment by id
        try:
            assessment = Assesment.objects.get(id=assessment_id)
        except Assesment.DoesNotExist:
            return Response({"error": "Assessment not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if quote_id is provided, and if so, link it to the assessment
        if 'quote_id' in request.data:
            try:
                quote = Quote.objects.get(id=request.data['quote_id'])
                # Associate quote with the assessment
                assessment.quote = quote
            except Quote.DoesNotExist:
                return Response({"error": "Quote not found."}, status=status.HTTP_404_NOT_FOUND)

        # Update the accessor in the assessment
        assessment.accessor = accessor

        # Update other fields with the provided data
        serializer = AssessmentSerializer(assessment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PlaceBidView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=BidSerializer)
    def post(self, request, quote_id=None):
        # Ensure the user is an assessor
        try:
            assessor = Accessor.objects.get(user=request.user)
        except Accessor.DoesNotExist:
            return Response({"error": "You are not authorized to place a bid."}, status=status.HTTP_403_FORBIDDEN)

        # Validate the quote
        try:
            quote = Quote.objects.get(id=quote_id)
        except Quote.DoesNotExist:
            return Response({"error": "Quote not found."}, status=status.HTTP_404_NOT_FOUND)

        # Validate the quote status (optional)
        if quote.status != 'pending':
            return Response({"error": "Bids can only be placed on quotes with 'pending' status."}, status=status.HTTP_400_BAD_REQUEST)

        # Create the bid
        data = request.data
        bid = Bid.objects.create(
            amount=data.get('amount'),
            availability=data.get('availability'),
            VAT_Registered=data.get('VAT_Registered', False),
            SEAI_Registered=data.get('SEAI_Registered', False),
            insurance=data.get('insurance', False),
            assessor=assessor,
            quote=quote,
        )

        return Response({"message": "Bid placed successfully.", "bid_id": bid.id}, status=status.HTTP_201_CREATED)





                                ######### ADMIN VIEWS ############


class TotalAccessorsView(APIView):
    permission_classes = [IsAdminUser]  # Restrict access to admins only

    def get(self, request):
        total_accessors = Accessor.objects.count()  # Count all accessors
        return Response({"total_accessors": total_accessors}, status=status.HTTP_200_OK)


class TotalClientsView(APIView):
    permission_classes = [IsAdminUser]  # Restrict access to admins only

    def get(self, request):
        total_clients = Client.objects.count()  # Count all clients
        return Response({"total_clients": total_clients}, status=status.HTTP_200_OK)


class TotalPendingJobsView(APIView):
    permission_classes = [IsAdminUser]  # Restrict access to admins only

    def get(self, request):
        total_pending_jobs = Job.objects.filter(status__iexact="Pending").count()  # Count jobs with status 'Pending'
        return Response({"total_pending_jobs": total_pending_jobs}, status=status.HTTP_200_OK)


class ACDetailsView(APIView):
    permission_classes = [IsAdminUser]  # Restrict access to admins only

    def get(self, request):
        # Annotate clients with the count of jobs they have
        clients = Client.objects.annotate(job_count=Count('job', filter=Q(job__status='pending'))).values(
            'id', 'first_name', 'last_name', 'email', 'job_count'
        )

        # Transform the queryset into a list of client details
        client_details = [
            {
                "id": client['id'],
                "name": f"{client['first_name']} {client['last_name']}",
                "email": client['email'],
                "job_count": client['job_count']
            }
            for client in clients
        ]

        return Response(client_details, status=status.HTTP_200_OK)

class BMDetailsView(APIView):
    def get(self, request):
        # Count the total number of quotes
        total_quotes = Quote.objects.count()

        return Response({"total_quotes": total_quotes}, status=status.HTTP_200_OK)

class ClientDetailView(RetrieveAPIView):
    permission_classes = [IsAdminUser]  # Restrict access to admins only
    queryset = Client.objects.all()  # Get all clients
    serializer_class = ClientSerializer  # Use the serializer to return the data
    lookup_field = 'id'  # Use 'id' to look up the client in the URL

    def get(self, request, *args, **kwargs):
        client = self.get_object()  # Retrieve the client object by 'id'
        return Response({
            "id": client.id,
            "first_name": client.first_name,
            "last_name": client.last_name,
            "email": client.email,
            "phone_number": client.phone_number,
            "address": client.address,
        }, status=status.HTTP_200_OK)


class AdminJobAndQuoteView(APIView):
    permission_classes = [IsAdminUser]  # Only admin users can access this view

    def get(self, request):
        """
        Get specific fields from both Job and GetQuote models.
        Admin users only.
        """
        # Retrieve jobs and select only the required fields
        jobs = Job.objects.only(
            'id', 'created_at', 'county', 'building_type', 'property_size',
            'bedrooms', 'heat_pump_installed', 'ber_purpose', 'additional_features',
            'preferred_date', 'status'
        )

        # Retrieve get quotes and select only the required fields
        quotes = Quote.objects.only(
            'id', 'created_at', 'county', 'building_type', 'property_size',
            'bedrooms', 'heat_pump_installed', 'ber_purpose', 'additional_features',
            'preferred_date', 'status'
        )

        # Serialize the data using serializers
        job_serializer = TableJob(jobs, many=True)
        quote_serializer = QuoteSerializer(quotes, many=True)

        # Combine both job and quote data
        data = {
            'jobs': job_serializer.data,
            'quotes': quote_serializer.data,
        }

        return Response(data, status=status.HTTP_200_OK)


class BerMemberView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        # Annotate data with counts of projects grouped by accessor
        accessor_data = (
            Accessor.objects.values("id", "user__first_name", "user__last_name", "user__email", "user__is_active")
            .annotate(total_projects=Count("projects"))
            .order_by("user__first_name", "user__last_name")
        )

        # Prepare the response
        response_data = []
        for data in accessor_data:
            response_data.append({
                "name": f"{data['user__first_name']} {data['user__last_name']}",
                "email": data["user__email"],
                "total_projects": data["total_projects"],
                "is_active": data["user__is_active"],
            })

        return Response({
            "accessor_details": response_data,
        })


        ################################# Email NOTIFICATIONS ###########################


####### view to send post request on activation url###################
# class ActivateAccessorAPIView(APIView):
#     """ Activates an accessor account when a valid token is provided via POST. """
#
#     def post(self, request, token, *args, **kwargs):
#         user = get_object_or_404(UserModel, accessor_token=token, user_type='accessor')
#
#         if user.is_active:
#             return Response({"message": "User is already active."}, status=status.HTTP_400_BAD_REQUEST)
#
#         user.is_active = True
#         user.save(update_fields=['is_active'])
#
#         return Response({"message": "Account activated successfully."}, status=status.HTTP_200_OK)


class ActivateAccessorAPIView(APIView):
    """Activates an accessor account when a valid token is provided via POST."""

    def get(self, request, token, *args, **kwargs):
        """Auto-submit a POST request using JavaScript when the user visits the link."""
        html_response = f"""
        <html>
            <body>
                <script>
                    fetch("{request.build_absolute_uri()}", {{
                        method: "POST"
                    }}).then(response => response.json())
                    .then(data => {{
                        alert(data.message);
                    }})
                    .catch(error => console.error("Error:", error));
                </script>
                <p>Activating your account...</p>
            </body>
        </html>
        """
        return HttpResponse(html_response)

    def post(self, request, token, *args, **kwargs):
        """Activate the account when a POST request is made."""
        user = get_object_or_404(UserModel, accessor_token=token, user_type='accessor')

        if user.is_active:
            return Response({"message": "User is already active."}, status=status.HTTP_400_BAD_REQUEST)

        user.is_active = True
        user.save(update_fields=['is_active'])

        return Response({"message": "Account activated successfully."}, status=status.HTTP_200_OK)


class ForgotPasswordRequestAPIView(APIView):
    """
    Endpoint where accessors and admins can request a password reset.
    A 4-digit PIN is generated and stored in the user model.
    """
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        user = get_object_or_404(UserModel, email=email, user_type__in=['accessor', 'admin'])

        # Generate a 4-digit PIN
        pin = str(random.randint(1000, 9999))
        user.pin = pin
        user.pin_created_at = now()
        user.save(update_fields=['pin', 'pin_created_at'])

        return Response({"message": "A PIN has been generated and will be sent to your email.", "email": user.email}, status=status.HTTP_200_OK)


class ResetPasswordAPIView(APIView):
    """
    Endpoint where users submit the PIN and new password to reset their account.
    """

    def post(self, request, *args, **kwargs):
        pin = request.data.get('pin')
        new_password = request.data.get('new_password')

        user = get_object_or_404(UserModel, pin=pin, user_type__in=['accessor', 'admin'])

        # Check if the PIN is still valid (created less than 2 minutes ago)
        if user.pin_created_at and now() - user.pin_created_at > timedelta(minutes=2):
            return Response({"message": "PIN has expired."}, status=status.HTTP_400_BAD_REQUEST)

        # Reset password and clear PIN
        user.password = make_password(new_password)
        user.pin = None
        user.save(update_fields=['password', 'pin'])

        return Response({"message": "Password has been successfully reset."}, status=status.HTTP_200_OK)




################ NOT USED ########################
class JobListView(APIView):
    """
    View to list all jobs.
    """

    def get(self, request):
        jobs = Job.objects.all()
        serializer = JobSerializer(jobs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class FileDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        """
        Retrieve all files for a specific project.
        """
        user = request.user
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response({"error": "Project not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if the user is either a client or accessor associated with the project
        if request.user != project.client.user and request.user != project.accessor.user:
            raise PermissionDenied("You are not authorized to view files for this project.")

        # Get files associated with the project
        files = File.objects.filter(project=project)
        serializer = FileSerializer(files, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=FileSerializer)
    def post(self, request, project_id):
        """
        Upload a new file to a specific project.
        """
        # Fetch the project to which the file is being uploaded
        project = get_object_or_404(Project, id=project_id)

        # Check if the user is either the client or accessor associated with the project
        if request.user != project.client.user and request.user != project.accessor.user:
            raise PermissionDenied("You are not authorized to upload files for this project.")

        # Proceed with file upload if the user is authorized
        serializer = FileSerializer(data=request.data)
        if serializer.is_valid():
            # Automatically associate the file with the project
            serializer.save(project=project)  # Ensure the file is associated with the project
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(request_body=FileSerializer)
    def put(self, request, pk):
        """
        Update an existing file's details (e.g., file type).
        """
        user = request.user

        try:
            # Check if the user is a client
            client = Client.objects.get(user=user)
            file = File.objects.get(id=pk, project__client=client)  # Ensure file is associated with the client's project
        except Client.DoesNotExist:
            try:
                # Check if the user is an accessor
                accessor = Accessor.objects.get(user=user)
                file = File.objects.get(id=pk, project__accessor=accessor)  # Ensure file is associated with the accessor's project
            except Accessor.DoesNotExist:
                return Response({"error": "User is neither a client nor an accessor."}, status=status.HTTP_403_FORBIDDEN)
            except File.DoesNotExist:
                return Response({"error": "File not found or you are not authorized to update it."}, status=status.HTTP_404_NOT_FOUND)

        # Proceed with updating file details
        serializer = FileSerializer(file, data=request.data, partial=True)  # partial=True allows updating only the provided fields
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(request_body=FileSerializer)
    def delete(self, request, pk):
        """
        Delete a specific file.
        """
        user = request.user

        try:
            # Check if the user is a client
            client = Client.objects.get(user=user)
            file = File.objects.get(id=pk, project__client=client)  # Ensure file is associated with the client's project
        except Client.DoesNotExist:
            try:
                # Check if the user is an accessor
                accessor = Accessor.objects.get(user=user)
                file = File.objects.get(id=pk, project__accessor=accessor)  # Ensure file is associated with the accessor's project
            except Accessor.DoesNotExist:
                return Response({"error": "User is neither a client nor an accessor."}, status=status.HTTP_403_FORBIDDEN)
            except File.DoesNotExist:
                return Response({"error": "File not found or you are not authorized to delete it."}, status=status.HTTP_404_NOT_FOUND)

        # Delete the file
        file.delete()
        return Response({"message": "File deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

