from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework.generics import ListAPIView
from .models import BackgroundMainPage, AstroImage
from .serializers import BackgroundMainPageSerializer, AstroImageSerializer

# Create your views here.

class AstroImageListView(ListAPIView):
    """View to list all astrophotography images."""
    queryset = AstroImage.objects.all().order_by('-capture_date')
    serializer_class = AstroImageSerializer

class BackgroundMainPageView(ViewSet):
    def list(self, request):
        instance = BackgroundMainPage.objects.order_by('-created_at').first()
        if instance:
            serializer = BackgroundMainPageSerializer(instance, context={'request': request})
            return Response(serializer.data)
        return Response({'url': None})
