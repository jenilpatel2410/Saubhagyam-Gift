from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from ..models import UserModel
from ..serializers import MobileUserSerializer
from management_app.pagination import ListPagination
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from xhtml2pdf import pisa
from django.conf import settings
from django.template.loader import render_to_string
import os
from datetime import datetime

class CustomerListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = ListPagination
    filter_backends = [SearchFilter]
    search_fields = ['first_name','last_name', 'email','mobile_no']
    def get(self, request):
        
        role_type = request.query_params.get('role_type')
        search = request.query_params.get('search', '').strip()
        is_pdf = request.query_params.get("is_pdf", False)
        
        if role_type and role_type not in ['Admin', 'Employee', 'Distributer', 'Retailer', 'Wholesaler']:
            return Response({
                'status': False,
                'message' : 'Invalid role Type',
                'errors' : 'Error in Role Type'
            })
            
        if role_type :
            customers = UserModel.objects.filter(role__type = role_type).order_by('-id')
        else:
            customers = UserModel.objects.filter(
                role__type__in=["Retailer", "Wholesaler"]
            ).order_by('-id')
            
        # Apply search manually
        if search:
            query = Q()
            for field in self.search_fields:
                query |= Q(**{f"{field}__icontains": search})
            customers = customers.filter(query)
        
        items = list(customers)

        paginator = ListPagination()
        paginated_customers = paginator.paginate_queryset(items, request)
        
        all_records = self.request.query_params.get('all', False)
        if all_records and all_records in ['1', 'true', 'True', True]:
            paginated_customers = None
            
        if is_pdf in ['1', 'true', 'True', True]:
            serializer = MobileUserSerializer(paginated_customers, many=True)
            return self.generate_pdf(serializer.data, request)
            
        if paginated_customers is not None:
            serializer = MobileUserSerializer(paginated_customers, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        serializer = MobileUserSerializer(items, many=True)
        return Response({
            "status": True,
            "data": serializer.data,
            "message": "customer list Successfully."
        }, status=status.HTTP_200_OK)
        
    def generate_pdf(self, customers, request):
        try:
            html_content = render_to_string(
                "customer_pdf_template.html",
                {"customers": customers},
            )

            # Ensure export directory exists
            export_dir = os.path.join(settings.MEDIA_ROOT, "export", "customer_pdf")
            os.makedirs(export_dir, exist_ok=True)

            # Generate unique filename
            file_name = f'customers_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
            file_path = os.path.join(export_dir, file_name)

            # Create PDF
            with open(file_path, "wb") as pdf_file:
                pisa_status = pisa.CreatePDF(html_content, dest=pdf_file)

            if pisa_status.err:
                return Response({"status": False, "message": "Error generating PDF"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Build download URL
            file_uri = os.path.join(settings.MEDIA_URL, "export", "customer_pdf", file_name)
            absolute_file_uri = request.build_absolute_uri(file_uri)

            return Response({
                "status": True,
                "file_uri": absolute_file_uri,
                "message": "Customer PDF successfully generated"
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"status": False, "message": f"PDF Error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
