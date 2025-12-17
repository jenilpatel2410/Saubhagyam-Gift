from django.db.models import Q
from django.http import Http404, HttpResponse
from django.utils.text import slugify
from ..models import *
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
# from rest_framework import filters,generics
from management_app.serializer.InquirySerializer import *
from rest_framework.permissions import IsAuthenticated

class InquiryList(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        queryset = request.data.get("inquiry", request.data)  

        if not queryset:
            return Response({
                "status": False,
                "message": "Inquiry data is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = InquirySerializer(data=queryset)
        if serializer.is_valid():
            inquiry = serializer.save()
            return Response({
                "status": True,
                "message": "Your inquiry has been sent successfully",
                "data": InquirySerializer(inquiry).data
            }, status=status.HTTP_200_OK)

        return Response({
            "status": False,
            "message": "Validation error",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
