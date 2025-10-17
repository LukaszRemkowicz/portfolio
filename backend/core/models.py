from django.db import models

class BaseImage(models.Model):
    """Base abstract model for images"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    path = models.ImageField(upload_to='images/')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def __str__(self):
        return self.name 