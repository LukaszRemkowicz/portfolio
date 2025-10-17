from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from django.conf import settings
from django.core.mail import send_mail

from .models import ContactMessage
from .serializers import ContactMessageSerializer


class ContactMessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling contact messages
    """

    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer

    def get_permissions(self):
        """
        Allow anyone to create contact messages,
        but require authentication for other actions
        """
        if self.action == "create" or self.action == "submit_contact_form":
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def create(self, request, *args, **kwargs):
        """
        Create a new contact message and send email notification
        """
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    "message": "Please correct the errors below.",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Save the message to database (only reached if validation passes)
        contact_message = serializer.save()

        # Send email notification
        try:
            self.send_contact_notification_email(contact_message)
        except Exception as e:
            # Log the error but don't fail the request
            print(f"Failed to send email notification: {e}")

        return Response(
            {
                "message": "Thank you! Your message has been sent successfully.",
                "id": contact_message.id,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def mark_as_read(self, request, pk=None):
        """
        Mark a contact message as read
        """
        contact_message = self.get_object()
        contact_message.is_read = True
        contact_message.save()

        return Response({"message": "Message marked as read", "id": contact_message.id})

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def unread_count(self, request):
        """
        Get count of unread messages
        """
        count = ContactMessage.objects.filter(is_read=False).count()
        return Response({"unread_count": count})

    def send_contact_notification_email(self, contact_message):
        """
        Send email notification for new contact messages
        """
        subject = f"New Contact Message: {contact_message.subject}"
        message = f"""
        New contact message received:

        From: {contact_message.name} ({contact_message.email})
        Subject: {contact_message.subject}
        Message: {contact_message.message}

        Received at: {contact_message.created_at}
        """

        # Get email settings from Django settings
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@example.com")
        to_email = getattr(settings, "CONTACT_EMAIL", "admin@example.com")

        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=[to_email],
            fail_silently=False,
        )
