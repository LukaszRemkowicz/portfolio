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
        ]
        read_only_fields = ["id"]

    def validate_website(self, value: Optional[str]) -> str:
        """Honeypot validation - if filled, it's a bot"""
        if value:
            raise serializers.ValidationError("Bot detected.")
        return value or ""

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """Additional validation for contact message"""
        attrs.pop("website", None)
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
        stripped_value = value.strip()
        if len(stripped_value) < 10:
            raise serializers.ValidationError("Message must be at least 10 characters long.")
        if len(stripped_value) > 5000:
            raise serializers.ValidationError("Message is too long (max 5000 characters).")
        return stripped_value

    def validate_email(self, value: str) -> str:
        """Validate email field"""
        if not value or "@" not in value:
            raise serializers.ValidationError("Please provide a valid email address.")
        return value.lower().strip()
