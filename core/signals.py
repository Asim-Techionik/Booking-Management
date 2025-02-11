import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.utils.timezone import now
from .models import UserModel, Notification
from django.conf import settings
from core.email_backend import send_gmail_api

logger = logging.getLogger(__name__)  # ✅ Setup logging

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

            Please approve or reject their application.

            Best regards,
            Your System
            """
            logger.info(f"📨 Sending email to {admin_email}")
            send_gmail_api(subject, message, admin_email)
            logger.info(f"✅ Email sent to {admin_email}")
