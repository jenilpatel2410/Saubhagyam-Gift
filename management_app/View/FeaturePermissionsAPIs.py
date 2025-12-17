from rest_framework.response import Response
from rest_framework import status
from management_app.serializer.FeaturePermissionSerializer import *
from ..models import *
from user_app.models import *
from django.utils.text import slugify
from rest_framework.views import APIView
from django.db.models import Q
from django.conf import settings
import csv
import openpyxl
from django.http import HttpResponse
from openpyxl.styles import Font
import reportlab
import requests
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from django.utils.timezone import localtime
from ..pagination import ListPagination



class FeaturePermissionView(APIView):
    def get(self, request):
        # Fetch all top-level features (depth=1)
        root_features = FeatureModel.objects.filter(depth=1)

        # Preload permissions + roles efficiently
        feature_permissions = FeatureApplication.objects.select_related('feature', 'role')

        # Get all unique role types
        role_types = RoleModel.objects.values_list('type', flat=True).distinct()

        feature_p = {}

        for role_type in role_types:
            # Get all permission objects for this role
            role_perms = feature_permissions.filter(role__type=role_type)

            # Map: feature_id → permission flags
            perm_map = {
                p.feature_id: {
                    "is_viewed": p.is_viewed if role_type != 'Admin' else True,
                    "is_read": p.is_read if role_type != 'Admin' else True,
                    "is_write": p.is_write if role_type != 'Admin' else True,
                    "is_delete": p.is_delete if role_type != 'Admin' else True,
                }
                for p in role_perms
            }

            def serialize_feature_with_perms(feature):
                """Recursively build feature tree with permissions for this role"""
                perm = perm_map.get(
                    feature.id,
                    {   # Default False if not in FeatureApplication
                        "is_viewed": False if role_type != 'Admin' else True,
                        "is_read": False if role_type != 'Admin' else True,
                        "is_write": False if role_type != 'Admin' else True,
                        "is_delete": False if role_type != 'Admin' else True,
                    }
                )
                return {
                    "id": feature.id,
                    "feature_module": feature.name,
                    "path": feature.full_path,
                    "children": [serialize_feature_with_perms(child) for child in feature.get_children()],
                    "is_viewed": perm["is_viewed"],
                    "is_read": perm["is_read"],
                    "is_write": perm["is_write"],
                    "is_delete": perm["is_delete"],
                    "role": role_type,
                    "feature": feature.id,
                }

            # Build tree for this role
            feature_p[role_type] = [serialize_feature_with_perms(f) for f in root_features]

        # # If Admin not present, build it manually (full access)
        # if 'Admin' not in feature_p and 'Administrator' not in feature_p:
        #     def serialize_admin_feature(feature):
        #         return {
        #             "id": feature.id,
        #             "feature_module": feature.name,
        #             "path": feature.full_path,
        #             "children": [serialize_admin_feature(child) for child in feature.get_children()],
        #             "is_viewed": True,
        #             "is_read": True,
        #             "is_write": True,
        #             "is_delete": True,
        #             "role": "Admin",
        #             "feature": feature.id,
        #         }

        #     feature_p['Admin'] = [serialize_admin_feature(f) for f in root_features]

        return Response(
            {
                'status': True,
                'data': feature_p,
                'message': 'Feature Permissions Successfully displayed',
            },
            status=status.HTTP_200_OK
        )
        
    def post(self, request):
        """
        Create or update feature permissions for a role.
        """
        permissions = request.data.get("permissions", [])
        if not permissions:
            return Response(
                {"status": False, "message": "permissions list is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            for item in permissions:
                role_id = item.get("role")
                feature_id = item.get("feature")

                if not role_id or not feature_id:
                    continue

                # Create or update each record
                FeatureApplication.objects.update_or_create(
                    role_id=role_id,
                    feature_id=feature_id,
                    defaults={
                        "is_viewed": item.get("is_viewed", False),
                        "is_read": item.get("is_read", False),
                        "is_write": item.get("is_write", False),
                        "is_delete": item.get("is_delete", False),
                    },
                )
            return Response(
                {"status": True, "message": "Feature permissions saved successfully"},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"status": False, "message": f"Error saving permissions: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def patch(self, request, id=None):
        """
        Bulk update feature permissions.
        """
        permissions = request.data.get("permissions", [])
        if not permissions:
            return Response(
                {"status": False, "message": "permissions list is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            for item in permissions:
                role_id = item.get("role")
                feature_id = item.get("feature")
                if not role_id or not feature_id:
                    continue

                # Update existing or create if missing
                FeatureApplication.objects.update_or_create(
                    role_id=role_id,
                    feature_id=feature_id,
                    defaults={
                        "is_viewed": item.get("is_viewed", False),
                        "is_read": item.get("is_read", False),
                        "is_write": item.get("is_write", False),
                        "is_delete": item.get("is_delete", False),
                    },
                )
            return Response(
                {"status": True, "message": "Feature permissions updated successfully"},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"status": False, "message": f"Error updating permissions: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        
    def delete(self,request,id):
        try:
            feature_permission = FeatureApplication.objects.get(id=id)
            feature_permission.delete()
            return Response({'status':True,'message':'Feature Permission deleted successfully'},status=status.HTTP_200_OK)
        except FeatureApplication.DoesNotExist:
            return Response({'status':False,'message':'Permission not available'})