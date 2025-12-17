from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.utils.text import slugify
from ..models import CategoryModel
from management_app.translator import translate_text as t
from management_app.translator import get_lang_code

class WebCategoryListAPI(APIView):
    def get(self, request):
        lang = get_lang_code(request)
        data = []
        # Fetch only top-level parent categories
        parents = CategoryModel.get_root_nodes().filter(is_active=True).order_by('id')

        for parent in parents:
            # Check for translation
            translation = parent.translations.filter(language_code=lang).first()
            parent_name = translation.name if translation else parent.name

            parent_data = {
                "id": parent.id,
                "parent_category_name": parent_name.title(),
                "slug": slugify(parent.name),
                "encrypted_id": parent.encrypted_id,
                "child_category": []
            }

            # Get direct children of the parent category
            children = parent.get_children().filter(is_active=True).order_by('id')
            for child in children:
                child_translation = child.translations.filter(language_code=lang).first()
                child_name = child_translation.name if child_translation else child.name

                parent_data["child_category"].append({
                    "id": child.id,
                    "name": child_name.title(),
                    "slug": slugify(child.name),
                    "encrypted_id": child.encrypted_id,
                    "parent_id": parent.id
                })

            data.append(parent_data)

        return Response({
            'status': True,
            'data': data,
            'message': t('Categories successfully displayed')
        }, status=status.HTTP_200_OK)
