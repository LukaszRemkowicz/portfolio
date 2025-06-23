from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework.generics import ListAPIView
from .models import BackgroundMainPage, AstroImage
from .serializers import BackgroundMainPageSerializer, AstroImageSerializer

# Create your views here.

class AstroImageListView(ListAPIView):
    """View to list all astrophotography images, with optional filtering by celestial_object."""
    serializer_class = AstroImageSerializer

    def get_queryset(self):
        queryset = AstroImage.objects.all().order_by('-capture_date')
        filter_value = self.request.GET.get('filter')
        if filter_value:
            queryset = queryset.filter(celestial_object=filter_value)
        return queryset

class BackgroundMainPageView(ViewSet):
    def list(self, request):
        instance = BackgroundMainPage.objects.order_by('-created_at').first()
        if instance:
            serializer = BackgroundMainPageSerializer(instance, context={'request': request})
            return Response(serializer.data)
        return Response({'url': None})
