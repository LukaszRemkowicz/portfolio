from rest_framework import permissions, viewsets

from .models import Project
from .serializers import ProjectSerializer


class ProjectViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing programming projects.
    """

    queryset = Project.objects.all().prefetch_related("images")
    serializer_class = ProjectSerializer
    permission_classes = [permissions.AllowAny]
