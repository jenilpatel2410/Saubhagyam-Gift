from django.db.models import Q
from django.http import Http404, HttpResponse
from django.utils.text import slugify
from ..models import *
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework import filters,generics
from management_app.serializer.VersionCheckSerializer import *

class VersionList(APIView):
    def post(self,request):
        # queryset=VersionModel.objects.all()
        queryset = VersionModel.objects.filter(android_status="0").order_by("-created_at")
        version =queryset.first()
        serialized = VesioncheckSerializer(version)
        data = {
            "status":True,
            "message":"Version retrived successfully",
            "data": serialized.data
        }
        return Response(data,status=status.HTTP_200_OK)