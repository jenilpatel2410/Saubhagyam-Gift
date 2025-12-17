from rest_framework.response import Response
from rest_framework import status
from ..serializers import *
from user_app.models import *
# from sales_client_app.paginations import WebProductPaginationClass
from django.utils.text import slugify
from django.conf import settings
from rest_framework.views import APIView
from django.db.models import Q
import csv
import openpyxl
from django.http import HttpResponse
from openpyxl.styles import Font
from ..pagination import ListPagination

class RoleAPI(APIView):

    def get(self,request):
        roles = RoleModel.objects.all().order_by('-id')
        search = request.query_params.get('search','')
        if search:
            roles = RoleModel.objects.filter(Q(name__icontains=search)
                                             )
        paginator = ListPagination()
        paginated_roles = paginator.paginate_queryset(roles,request)
        serializer = RoleSerilaizer(paginated_roles,many=True)
        return paginator.get_paginated_response(serializer.data)
    
    def post(self,request):
        data=request.data
        serializer = RoleSerilaizer(data=data)  
        if serializer.is_valid():
            serializer.save()
            return Response({'status':True,'data':serializer.data,'message':'Role Successfully added'})
        return Response({'status':False,'errors':serializer.errors})
    
    def patch(self,request,id):
        try:
            role = RoleModel.objects.get(id=id)
            serializer = RoleSerilaizer(role,data=request.data,partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'status':True,'data':serializer.data,'message':'Role Successfully updated'},status=status.HTTP_200_OK)
            return Response({'status':False,'errors':serializer.errors},status=status.HTTP_400_BAD_REQUEST)
        
        except RoleModel.DoesNotExist:
            return Response({'status':False,'message':'Role not Available'},status=status.HTTP_400_BAD_REQUEST)

    def delete(self,request,id):
        try :
            role = RoleModel.objects.get(id=id)
            role.delete()
            return Response({'status':True,'message':'Role successfully deleted'})
        except RoleModel.DoesNotExist:
           return Response({'status':False,'message':'Role not available'},status=status.HTTP_400_BAD_REQUEST)
        

class Export_role_excel(APIView):
    def get(self,request):
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "Roles"

        export_dir = os.path.join(settings.MEDIA_ROOT, 'export', 'roles')
        os.makedirs(export_dir, exist_ok=True)

        file_name = f'roles{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        file_path = os.path.join(export_dir, file_name)

        # header row
        sheet.append(["ID", "Name","Type"])
        for cell in sheet[1]:  # first row
            cell.font = Font(bold=True)

        # data rows
        for role in RoleModel.objects.all():
            sheet.append([role.id, role.name,role.type])

        workbook.save(file_path)        

        file_uri = os.path.join(settings.MEDIA_URL, "export", "roles", file_name)
        absolute_file_uri = request.build_absolute_uri(file_uri)

        return Response({
            "status": True,
            "file_uri": absolute_file_uri,
            "message": "Roles successfully exported"
        }, status=200)
    

