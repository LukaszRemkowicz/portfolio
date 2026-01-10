# backend/inbox/serializers.py
from typing import Any, Dict, Optional

from rest_framework import serializers

from .models import ContactMessage


class ContactMessageSerializer(serializers.ModelSerializer):
    """
    Serializer for ContactMessage model with honeypot field for bot protection
    """

    # Honeypot field - invisible to humans, bots will fill it
    website = serializers.CharField(required=False, allow_blank=True, write_only=True)

    class Meta:
        model = ContactMessage
        fields = [
            "id",
            "name",
            "email",
            "subject",
            "message",
            "website",
            "created_at",
            "is_read",
        ]
        read_only_fields = ["id", "created_at", "is_read"]

    def validate_website(self, value: Optional[str]) -> str:
        """Honeypot validation - if filled, it's a bot"""
        if value:
            raise serializers.ValidationError("Bot detected.")
        return value or ""

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """Additional validation for message content"""
        attrs.pop("website", None)
        message: str = attrs.get("message", "")
        if len(message) > 5000:
            raise serializers.ValidationError(
                {"message": "Message is too long (max 5000 characters)."}
            )
        return attrs

    def validate_name(self, value: str) -> str:
        """Validate name field"""
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Name must be at least 2 characters long.")
        return value.strip()

    def validate_subject(self, value: str) -> str:
        """Validate subject field"""
        if len(value.strip()) < 5:
            raise serializers.ValidationError("Subject must be at least 5 characters long.")
        return value.strip()

    def validate_message(self, value: str) -> str:
        """Validate message field"""
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Message must be at least 10 characters long.")
        return value.strip()

    def validate_email(self, value: str) -> str:
        """Validate email field"""
        if not value or "@" not in value:
            raise serializers.ValidationError("Please provide a valid email address.")
        return value.lower().strip()


class ContactMessageListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing contact messages (admin use)
    """

    class Meta:
        model = ContactMessage
        fields = ["id", "name", "email", "subject", "created_at", "is_read"]
        read_only_fields = ["id", "created_at"]


class ContactMessageDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed contact message view (admin use)
    """

    class Meta:
        model = ContactMessage
        fields = [
            "id",
            "name",
            "email",
            "subject",
            "message",
            "created_at",
            "updated_at",
            "is_read",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
