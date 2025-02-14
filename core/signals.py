# import logging
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from django.contrib.contenttypes.models import ContentType
# from django.utils.timezone import now
# from .models import UserModel, Notification
# from django.conf import settings
# from core.email_backend import send_gmail_api
#
# logger = logging.getLogger(__name__)  # ✅ Setup logging
#
# @receiver(post_save, sender=UserModel)
# def handle_accessor_signup(sender, instance, created, **kwargs):
#     """Handles notifications & email alerts when an accessor signs up."""
#
#     if created and instance.user_type == 'accessor':
#         logger.info(f"📢 Signal Triggered: New accessor {instance.first_name} {instance.last_name} created!")
#
#         # 🔹 Find all admins
#         admin_users = UserModel.objects.filter(user_type='admin')
#
#         # 🔹 Create a notification for each admin
#         for admin in admin_users:
#             sender_content_type = ContentType.objects.get_for_model(instance)
#             Notification.objects.create(
#                 message=f"A new accessor {instance.first_name} {instance.last_name} has signed up and is waiting for approval.",
#                 notification_type="Accessor Signup",
#                 recipient=admin,
#                 sender_content_type=sender_content_type,
#                 sender_object_id=instance.id,
#                 status='unread',
#                 created_at=now(),
#             )
#
#         # 🔹 Send Email Notification to Admins
#         for admin in settings.ADMINS:
#             admin_email = admin[1]
#             subject = f"New Accessor Waiting for Approval: {instance.first_name} {instance.last_name}"
#             message = f"""
#             Hello Admin,
#
#             A new accessor has signed up and is waiting for approval. Please review their details:
#
#             Name: {instance.first_name} {instance.last_name}
#             Email: {instance.email}
#             Phone: {instance.phone_number}
#
#             Please approve or reject their application.
#
#             Best regards,
#             Your System
#             """
#             logger.info(f"📨 Sending email to {admin_email}")
#             send_gmail_api(subject, message, admin_email)
#             logger.info(f"✅ Email sent to {admin_email}")



from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
import logging
from .models import UserModel, Notification
from core.email_backend import send_gmail_api  # Assuming send_gmail_api is a function to send emails
import random


logger = logging.getLogger(__name__)

@receiver(post_save, sender=UserModel)
def handle_accessor_signup(sender, instance, created, **kwargs):
    """Handles notifications & email alerts when an accessor signs up."""

    if created and instance.user_type == 'accessor':
        logger.info(f"📢 Signal Triggered: New accessor {instance.first_name} {instance.last_name} created!")

        # 🔹 Find all admins
        admin_users = UserModel.objects.filter(user_type='admin')

        # 🔹 Create a notification for each admin
        for admin in admin_users:
            sender_content_type = ContentType.objects.get_for_model(instance)
            Notification.objects.create(
                message=f"A new accessor {instance.first_name} {instance.last_name} has signed up and is waiting for approval.",
                notification_type="Accessor Signup",
                recipient=admin,
                sender_content_type=sender_content_type,
                sender_object_id=instance.id,
                status='unread',
                created_at=now(),
            )

        # 🔹 Send Email Notification to Admins
        for admin in settings.ADMINS:
            admin_email = admin[1]
            subject = f"New Accessor Waiting for Approval: {instance.first_name} {instance.last_name}"
            message = f"""
            Hello Admin,

            A new accessor has signed up and is waiting for approval. Please review their details:

            Name: {instance.first_name} {instance.last_name}
            Email: {instance.email}
            Phone: {instance.phone_number}

            Activation URL: {instance.activation_url}

            Please approve or reject their application.

            Best regards,
            Your System
            """
            logger.info(f"📨 Sending email to {admin_email}")
            send_gmail_api(subject, message, admin_email)
            logger.info(f"✅ Email sent to {admin_email}")

        # 🔹 Send Activation Email to Accessor
        accessor_email = instance.email
        subject = "Activate Your Account"
        activation_message = f"""
        Hello {instance.first_name},

        Thank you for signing up as an accessor. To activate your account, please click the link below:

        {instance.activation_url}

        Best regards,
        Your Team
        """
        logger.info(f"📨 Sending activation email to {accessor_email}")
        send_gmail_api(subject, activation_message, accessor_email)
        logger.info(f"✅ Activation email sent to {accessor_email}")


@receiver(post_save, sender=UserModel)
def handle_password_reset_request(sender, instance, created, **kwargs):
    """Handles sending password reset PIN when a reset request is made."""
    if not created and instance.pin:  # Ensure it's an update, not a new user creation
        logger.info(f"📢 Password Reset Requested for {instance.email}")

        # Generate a 4-digit PIN if not already set
        if not instance.pin:
            instance.pin = str(random.randint(1000, 9999))
            instance.save(update_fields=['pin'])

        # Send Email with PIN
        subject = "Password Reset PIN"
        reset_message = f"""
        Hello {instance.first_name},

        You have requested to reset your password. Use the following PIN to reset it:

        PIN: {instance.pin}

        If you did not request this, please ignore this email.

        Best regards,
        Your Team
        """
        logger.info(f"📨 Sending password reset email to {instance.email}")
        send_gmail_api(subject, reset_message, instance.email)
        logger.info(f"✅ Password reset email sent to {instance.email}")
