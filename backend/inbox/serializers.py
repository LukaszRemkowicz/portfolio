from rest_framework import serializers

from .models import ContactMessage


class ContactMessageSerializer(serializers.ModelSerializer):
    """
    Serializer for ContactMessage model
    """

    class Meta:
        model = ContactMessage
        fields = ["id", "name", "email", "subject", "message", "created_at", "is_read"]
        read_only_fields = ["id", "created_at", "is_read"]

    def validate_name(self, value):
        """Validate name field"""
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Name must be at least 2 characters long.")
        return value.strip()

    def validate_subject(self, value):
        """Validate subject field"""
        if len(value.strip()) < 5:
            raise serializers.ValidationError("Subject must be at least 5 characters long.")
        return value.strip()

    def validate_message(self, value):
        """Validate message field"""
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Message must be at least 10 characters long.")
        return value.strip()

    def validate_email(self, value):
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
