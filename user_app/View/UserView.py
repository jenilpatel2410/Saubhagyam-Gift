from rest_framework.response import Response
from rest_framework import status
from ..serializers import *
from ..models import *
# from sales_client_app.paginations import WebProductPaginationClass
from django.utils.text import slugify
from django.conf import settings
from rest_framework.views import APIView
from django.db.models import Q, Value
from django.db.models.functions import Concat
import csv
import openpyxl
from openpyxl.styles import Font
from django.http import HttpResponse
from management_app.pagination import ListPagination


class AdminView(APIView):

    def get(self,request):
        admin = UserModel.objects.filter(role__type='Admin')
        serializer = UserListSerializer(admin,many=True)
        return Response({'status':True,'data':serializer.data,'message':'Admin successfully retrieved'})
    
    def post(self,request):
        data = request.data
        serializer = AdminSerializer(data=data,context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response({'status':True,'data':serializer.data,'message':'Admin Successfully added'})
        
        return Response({'status':False,'errors':serializer.errors})
    
    def patch(self,request,id):
        
        try:
            admin = UserModel.objects.get(id=id)
            serializer = AdminSerializer(admin,data=request.data,partial=True,context={"request": request})
            if serializer.is_valid():
                serializer.save()
                return Response({'status':True,'data':serializer.data,'message':'Admin Successfully updated'})
            
            return Response({'status':False,'errors':serializer.errors})
        except UserModel.DoesNotExist:
            return Response({'status':False,'message':'Admin does not exist'})
    
    def delete(self,request,id):
         try:
            admin = UserModel.objects.get(id=id)
            admin.delete()
            return Response({'status':True,'message':'Admin Successfully deleted'})
         except UserModel.DoesNotExist:
            return Response({'status':False,'message':'Admin does not exist'})


class UserView(APIView):

    def get(self,request,id=None):
        try:
            users = ContactModel.objects.all().annotate(full_name=Concat('user__first_name', Value(' '), 'user__last_name')).exclude(user__role__type='Admin').order_by('-id')
            search = request.query_params.get('search','')
            user_type = request.query_params.get('type','')
            filter = request.query_params.get('filter','')
            if id: 
                user = ContactModel.objects.get(id=id)
                serializer = UserListSerializer(user)
                return Response ({'status':True,'data':serializer.data})

            if filter:
                users = users.filter(user__role__type__icontains = filter)
            if user_type:
                if user_type == 'clients':
                    users = users.filter(user__role__type__in=['Retailer','Wholesaler'])
                else:
                    users = users.filter(user__role__type__iexact=user_type)
            if search:
                users = users.filter(
                Q(name__icontains=search) |
                Q(full_name__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__firm_name__icontains=search) |
                Q(email__icontains=search) |
                Q(user__role__type__icontains=search) |
                Q(phone_no__icontains=search)
            )
            paginator = ListPagination()
            paginated_users = paginator.paginate_queryset(users.order_by('user__firm_name'),request)
            serializer = UserListSerializer(paginated_users,many=True)
            return paginator.get_paginated_response(serializer.data)
        
        except ContactModel.DoesNotExist:
            return Response({'status':False,'message':'User does not exist'}, status=status.HTTP_404_NOT_FOUND)
                    
    
    def post(self,request):
        try:
            data = request.data
            mobile_no = request.data.get('mobile_no')
            if ProfileModel.objects.filter(mobile_no=mobile_no).exists():
                return Response({'status': False, 'message': 'Mobile number already exists'}, status=status.HTTP_400_BAD_REQUEST)
            serializer = UserSerializer(data=data)
            
            if not serializer.is_valid():
                errors = []
                for field, msgs in serializer.errors.items():
                    for msg in msgs:
                        errors.append(f"• {msg.title()}\n")
                return Response({'status':False,'message':errors}, status=status.HTTP_400_BAD_REQUEST)
            else:
                serializer.save()
                return Response({'status':True,'data':serializer.data,'message':'User Successfully added'},status = status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'status':False, 'message':str(e)
            }, status = status.HTTP_400_BAD_REQUEST)
    
    def patch(self,request,id):
        
        try:
            contact = ContactModel.objects.get(id=id)
            user = contact.user
            serializer = UserSerializer(user,data=request.data,partial=True)
            
            if not serializer.is_valid():
                errors = []
                for field, msgs in serializer.errors.items():
                    for msg in msgs:
                        errors.append(f"• {msg.title()}\n")
                return Response({'status':False,'message':errors}, status=status.HTTP_400_BAD_REQUEST)
            else:
                serializer.save()
                return Response({'status':True,'data':serializer.data,'message':'User Successfully updated'}, status=status.HTTP_200_OK)
            
        except ContactModel.DoesNotExist:
            return Response({'status':False,'message':'User does not exist'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'status':False, 'message':str(e)
            }, status = status.HTTP_400_BAD_REQUEST)
    
    def delete(self,request,id):
         try:
            contact = ContactModel.objects.get(id=id)
            user = contact.user
            user.delete()
            return Response({'status':True,'message':'User Successfully deleted'}, status=status.HTTP_200_OK)
         except ContactModel.DoesNotExist:
            return Response({'status':False,'message':'User does not exist'}, status=status.HTTP_404_NOT_FOUND)


class UserExportView(APIView):

    def get(self,request):
        user_type = request.query_params.get('type')
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "Users"

        export_dir = os.path.join(settings.MEDIA_ROOT, "export", "users")
        os.makedirs(export_dir, exist_ok=True)

        file_name = f'users{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        file_path = os.path.join(export_dir, file_name)

        
        users = ContactModel.objects.all()

        if user_type == 'clients':
            users = users.filter(user__role__type__in=['Retailer','Wholesaler'])
            sheet.append(['ID','Name','Firm Name','Email','Mobile No.','Role'])
            for cell in sheet[1]:  
                cell.font = Font(bold=True)
        else:
            users = users.filter(user__role__type__iexact='Employee')
            sheet.append(['ID','Name','Email','Mobile No.','Role'])
            for cell in sheet[1]:  
                cell.font = Font(bold=True)

        # data rows
        for user in users:
                row = [
                    user.id,
                    user.name,
                    user.email,
                    str(user.phone_no) or '',
                    user.user.role.type if user.user and user.user.role else '',
                ]
                if user_type == 'clients':
                    row.insert(2, user.user.firm_name if user.user and user.user.firm_name else '')
                sheet.append(row)

        workbook.save(file_path)


        file_uri = os.path.join(settings.MEDIA_URL, "export", "users", file_name)
        absolute_file_uri = request.build_absolute_uri(file_uri)

        return Response({
            "status": True,
            "file_uri": absolute_file_uri,
            "message": "Users successfully exported"
        }, status=200)
