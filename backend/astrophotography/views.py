# backend/astrophotography/views.py
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.viewsets import ViewSet

from core.throttling import APIRateThrottle

from .models import AstroImage, BackgroundMainPage
from .serializers import (
    AstroImageSerializer,
    AstroImageSerializerList,
    BackgroundMainPageSerializer,
)

# Create your views here.


class AstroImageListView(ListAPIView):
    """View to list all astrophotography images, with optional filtering."""

    serializer_class = AstroImageSerializerList
    throttle_classes = [APIRateThrottle, UserRateThrottle]

    def get_queryset(self):
        queryset = AstroImage.objects.all().order_by("-capture_date")
        filter_value = self.request.GET.get("filter")
        if filter_value:
            queryset = queryset.filter(celestial_object=filter_value)
        return queryset


class AstroImageDetailView(RetrieveAPIView):
    queryset = AstroImage.objects.all()
    serializer_class = AstroImageSerializer
    throttle_classes = [APIRateThrottle, UserRateThrottle]


class BackgroundMainPageView(ViewSet):
    throttle_classes = [APIRateThrottle, UserRateThrottle]

    def list(self, request: Request) -> Response:
        instance = BackgroundMainPage.objects.order_by("-created_at").first()
        if instance:
            serializer = BackgroundMainPageSerializer(instance, context={"request": request})
            return Response(serializer.data)
        return Response({"url": None})
