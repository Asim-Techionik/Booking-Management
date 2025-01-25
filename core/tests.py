# from rest_framework.test import APITestCase, APIClient
# from rest_framework import status
# from django.contrib.auth import get_user_model
# from .models import Job, Client, Accessor, Bid, Project, Notification
# from django.utils.timezone import now
#
# UserModel = get_user_model()
#
# class BaseTestCase(APITestCase):
#     def setUp(self):
#         # Create clients and accessors
#         self.client_user = UserModel.objects.create_user(
#             email='client@example.com', password='password123', user_type='client')
#         self.accessor_user = UserModel.objects.create_user(
#             email='accessor@example.com', password='password123', user_type='accessor')
#
#         self.client = Client.objects.create(user=self.client_user)
#         self.accessor = Accessor.objects.create(user=self.accessor_user)
#
#         # Create a job for testing
#         self.job = Job.objects.create(
#             title="Test Job", description="Test description", location="Test Location",
#             building_type="Residential", client=self.client, status='Pending'
#         )
#
#         # Create an APIClient instance
#         self.api_client = APIClient()
#
# class UserCreateTest(BaseTestCase):
#     def test_create_user_success(self):
#         url = '/api/user/create/'  # URL should match the one in your routing
#         data = {
#             'email': 'newuser@example.com',
#             'password': 'password123',
#             'confirm_password': 'password123',
#             'first_name': 'New',
#             'last_name': 'User',
#             'phone_number': '1234567890',
#             'user_type': 'client'
#         }
#
#         response = self.api_client.post(url, data)
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#         self.assertEqual(response.data['email'], 'newuser@example.com')
#
#     def test_create_user_password_mismatch(self):
#         url = '/api/user/create/'
#         data = {
#             'email': 'newuser@example.com',
#             'password': 'password123',
#             'confirm_password': 'wrongpassword',
#             'first_name': 'New',
#             'last_name': 'User',
#             'phone_number': '1234567890',
#             'user_type': 'client'
#         }
#
#         response = self.api_client.post(url, data)
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertIn("confirm_password", response.data)
#
# class UserLoginTest(BaseTestCase):
#     def test_user_login_success(self):
#         url = '/api/user/login/'  # URL should match the one in your routing
#         data = {
#             'email': 'client@example.com',
#             'password': 'password123'
#         }
#
#         response = self.api_client.post(url, data)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertIn('access', response.data)  # Checking if access token is returned
#
#     def test_user_login_failure(self):
#         url = '/api/user/login/'
#         data = {
#             'email': 'client@example.com',
#             'password': 'wrongpassword'
#         }
#
#         response = self.api_client.post(url, data)
#         self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
#         self.assertEqual(response.data['detail'], 'Invalid credentials')
#
# class JobViewTest(BaseTestCase):
#     def test_create_job(self):
#         url = '/api/job/'
#         data = {
#             'title': 'New Job',
#             'description': 'Description of the new job',
#             'location': 'Test Location',
#             'building_type': 'Residential',
#         }
#
#         self.api_client.force_authenticate(user=self.client_user)  # Log in as the client
#         response = self.api_client.post(url, data)
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#         self.assertEqual(response.data['title'], 'New Job')
#
#     def test_get_all_jobs(self):
#         url = '/api/job/'
#         self.api_client.force_authenticate(user=self.accessor_user)  # Log in as accessor
#         response = self.api_client.get(url)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#
#     def test_update_job(self):
#         url = f'/api/job/{self.job.id}/'
#         data = {'status': 'Completed'}
#
#         self.api_client.force_authenticate(user=self.client_user)  # Log in as the client
#         response = self.api_client.put(url, data)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(response.data['status'], 'Completed')
#
# class BidCreateTest(BaseTestCase):
#     def test_create_bid(self):
#         url = f'/api/job/{self.job.id}/bid/'
#         data = {
#             'amount': 5000,
#             'availability': 'Available',
#         }
#
#         self.api_client.force_authenticate(user=self.accessor_user)  # Log in as the accessor
#         response = self.api_client.post(url, data)
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#         self.assertEqual(response.data['amount'], 5000)
#
#     def test_create_bid_job_not_pending(self):
#         # Change job status to 'In Progress' and attempt to bid
#         self.job.status = 'In Progress'
#         self.job.save()
#
#         url = f'/api/job/{self.job.id}/bid/'
#         data = {'amount': 5000, 'availability': 'Available'}
#
#         self.api_client.force_authenticate(user=self.accessor_user)
#         response = self.api_client.post(url, data)
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertIn("Bids can only be placed", response.data['error'])
#
# class NotificationListTest(BaseTestCase):
#     def test_notification_list(self):
#         url = '/api/notifications/'
#
#         # Create a notification for the client
#         notification = Notification.objects.create(
#             message="You have a new bid.",
#             notification_type='bid',
#             sender=self.accessor,
#             recipient=self.client_user,
#         )
#
#         self.api_client.force_authenticate(user=self.client_user)  # Log in as the client
#         response = self.api_client.get(url)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(len(response.data), 1)
#         self.assertEqual(response.data[0]['message'], "You have a new bid.")
#
# class FileUploadTest(BaseTestCase):
#     def test_upload_file(self):
#         url = f'/api/project/{self.job.id}/file/upload/'
#
#         # Prepare a file for uploading (use an actual file or mock this)
#         file_data = {
#             'file': open('path_to_a_file', 'rb'),
#             'file_type': 'image',
#         }
#
#         self.api_client.force_authenticate(user=self.client_user)  # Log in as client
#         response = self.api_client.post(url, file_data, format='multipart')
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#
# class ProjectListTest(BaseTestCase):
#     def test_get_projects(self):
#         url = '/api/project/'
#
#         # Create a project
#         project = Project.objects.create(
#             job=self.job, client=self.client, accessor=self.accessor,
#             status='In Progress', start_date=now()
#         )
#
#         self.api_client.force_authenticate(user=self.client_user)  # Log in as client
#         response = self.api_client.get(url)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(len(response.data), 1)