# backend/astrophotography/views.py
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.viewsets import ReadOnlyModelViewSet, ViewSet

from core.throttling import APIRateThrottle

from .models import AstroImage, BackgroundMainPage
from .serializers import (
    AstroImageSerializer,
    AstroImageSerializerList,
    BackgroundMainPageSerializer,
)

# Create your views here.


class AstroImageViewSet(ReadOnlyModelViewSet):
    """
    ViewSet for listing and retrieving astrophotography images.
    Supports filtering by celestial_object via 'filter' query parameter.
    """

    throttle_classes = [APIRateThrottle, UserRateThrottle]

    def get_queryset(self):
        queryset = AstroImage.objects.all().order_by("-capture_date")
        filter_value = self.request.query_params.get("filter")
        if filter_value:
            queryset = queryset.filter(celestial_object=filter_value)
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return AstroImageSerializerList
        return AstroImageSerializer


class BackgroundMainPageView(ViewSet):
    throttle_classes = [APIRateThrottle, UserRateThrottle]

    def list(self, request: Request) -> Response:
        instance = BackgroundMainPage.objects.order_by("-created_at").first()
        if instance:
            serializer = BackgroundMainPageSerializer(instance, context={"request": request})
            return Response(serializer.data)
        return Response({"url": None})
