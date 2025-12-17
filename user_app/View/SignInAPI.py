from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import Group
from django.contrib.auth import authenticate, login, logout
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError, PermissionDenied
from user_app.models import *
from management_app.models import *
from uuid import uuid4
from django.core.mail import send_mail
from copy import deepcopy
from secrets import token_urlsafe
from dateutil.relativedelta import relativedelta
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from rest_framework.decorators import renderer_classes
from django.utils import timezone
from django.db.models import Q
import random
import string
from collections import defaultdict

class SignInView(APIView):
    def post(self, request, format=None):
        try:
            email = request.data['email']
            password = request.data['password']
           
            if UserModel.objects.get(email=email).is_active == True:
                auth_user = authenticate(username=email, password=password)
               
                if auth_user is not None and auth_user.role and auth_user.role.type in ['Admin', 'Employee']: 
                        data = dict()
                        obj, _ = Token.objects.get_or_create(user=auth_user)
                        login(request, auth_user)
                        data['id'] = auth_user.id
                        data['first_name'] = auth_user.first_name
                        data['last_name'] = auth_user.last_name
                        data['email'] = auth_user.email
                        data['token'] = obj.key

                        # --- Permission logic refactored ---
                        root_features = FeatureModel.objects.filter(depth=1)
                        all_permissions = FeatureApplication.objects.select_related('feature', 'role')
                        role_types = RoleModel.objects.values_list('type', flat=True).distinct()

                        feature_permissions = []

                        for role_type in role_types:
                            role_perms = all_permissions.filter(role__type=role_type)
                            
                            # Map feature_id → permission flags
                            perm_map = {
                                p.feature_id: {
                                    "is_viewed": p.is_viewed if role_type != 'Admin' else True,
                                    "is_read": p.is_read if role_type != 'Admin' else True,
                                    "is_write": p.is_write if role_type != 'Admin' else True,
                                    "is_delete": p.is_delete if role_type != 'Admin' else True,
                                }
                                for p in role_perms
                            }

                            def serialize_feature(feature):
                                perm = perm_map.get(feature.id, {
                                    "is_viewed": False if role_type != 'Admin' else True,
                                    "is_read": False if role_type != 'Admin' else True,
                                    "is_write": False if role_type != 'Admin' else True,
                                    "is_delete": False if role_type != 'Admin' else True,
                                })
                                return {
                                    "feature_module": feature.name,
                                    "path": feature.full_path,
                                    "children": [serialize_feature(child) for child in feature.get_children()],
                                    "is_viewed": perm["is_viewed"],
                                    "is_read": perm["is_read"],
                                    "is_write": perm["is_write"],
                                    "is_delete": perm["is_delete"],
                                    "component": feature.component,
                                    "icon": feature.icon,
                                    "role": role_type,
                                    "feature": feature.id
                                }

                            # Only include the current user's role
                            if auth_user.role.type == role_type:
                                feature_permissions = [serialize_feature(f) for f in root_features]

                        data['feature_permissions'] = feature_permissions
                                        
                        
                        return Response({'status': True, 'data': data, 'message': 'User successfully logged In'}, status=status.HTTP_200_OK)
                else:
                    return Response({'status': False, 'message': 'Invalid credentials!'}, status=status.HTTP_400_BAD_REQUEST)
                
                   
            else:
                return Response({'status': False, 'message': 'Your account has been deactivated!'}, status=status.HTTP_400_BAD_REQUEST)
        except UserModel.DoesNotExist:
            return Response({'status': False, 'message': 'Invalid credentials!'}, status=status.HTTP_400_BAD_REQUEST)
  

class LogoutView(APIView):
    def post(self, request, format=None):
        # if request.user.is_authenticated:
            logout(request)
            return Response({'status': True, 'message': 'User successfully logged out'}, status=status.HTTP_200_OK)
        # else:
        #     return Response({'status': False, 'message': 'Login is required'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)