from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from .models import BackgroundMainPage
from .serializers import BackgroundMainPageSerializer

# Create your views here.

class BackgroundMainPageView(ViewSet):
    def list(self, request):
        instance = BackgroundMainPage.objects.order_by('-created_at').first()
        if instance:
            serializer = BackgroundMainPageSerializer(instance, context={'request': request})
            return Response(serializer.data)
        return Response({'url': None})
