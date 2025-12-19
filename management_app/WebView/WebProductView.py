from rest_framework.response import Response
from rest_framework import status
from management_app.serializer.WebProductSerializer import WebProductSerializer
from management_app.models import ProductModel, CategoryModel,HomeCategoryModel,HomeCategoryTranslation, CategoryTranslation
from management_app.paginations import WebProductPaginationClass
from django.utils.text import slugify
from rest_framework.views import APIView
from django.db.models import Q
from management_app.translator import get_lang_code

class WebHomeProductView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            lang = get_lang_code(request)
            data = {}
            home_categories = HomeCategoryModel.objects.all().order_by('-id')
            for home_category in home_categories:
                translation = HomeCategoryTranslation.objects.filter(
                    home_category=home_category,
                    language_code=lang
                ).first()
                translated_name = translation.name if translation else home_category.name
                products = ProductModel.objects.filter(home_categories__name=home_category, is_published=True).distinct().order_by('-created_at')
                # data[category_name.lower().replace(' ','_')] = (WebProductSerializer(products[:6],many=True)).data #,context={'lang': lang, 'request': request})).data 
                
                data[home_category.name.lower().replace(' ', '_')] = {
                    "id": home_category.id,
                    "name": translated_name,
                    "data": WebProductSerializer(products[:6],many=True,context={'lang': lang, 'request': request}).data 
                }

            adv_serialized = WebProductSerializer(products[:2], many=True).data #,context={'lang': lang, 'request': request}).data
            for i, adv in enumerate(adv_serialized, start=1):
                adv['bg_image'] = f'/media/Categories/bg{i}.jpg'
            data['advertisemnt'] = adv_serialized
            
            parents_qs = CategoryModel.objects.filter(
                depth=1,
                is_active=True
            ).order_by('id')

            category_list = []

            for parent in parents_qs:
                category_translation = CategoryTranslation.objects.filter(
                    category=parent,
                    language_code=lang
                ).first()

                translated_cat_name = category_translation.name if category_translation else parent.name

                category_list.append({
                    'id': parent.id,
                    'encrypted_id': parent.encrypted_id,
                    'name': translated_cat_name,
                    'image': request.build_absolute_uri(parent.image.url) if parent.image else None,
                    'slug': parent.name.lower().replace(' ', '-'),
                    'has_children': parent.get_children().exists()
                })
                
                title_translation = {
                'en': 'Popular Categories',
                'hi': 'लोकप्रिय श्रेणियाँ',
                'mr': 'लोकप्रिय श्रेण्या',
                'gu': 'લોકપ્રિય કેટેગરીઓ',
                'bn': 'জনপ্রিয় বিভাগসমূহ',
                'ta': 'பிரபலமான வகைகள்',
                'te': 'ప్రచారంలో ఉన్న వర్గాలు',
                'kn': 'ಜನಪ್ರಿಯ ವರ್ಗಗಳು',
                'ml': 'ജനപ്രിയ വിഭാഗങ്ങൾ',
                'pa': 'ਲੋਕਪ੍ਰਿਯ ਸ਼੍ਰੇਣੀਆਂ'
            }

            data['categories'] = {
                "name": title_translation.get(lang, 'Popular Categories'),
                "data": category_list
            }
                # if parent and parent.name not in parent_name_set:
                #     parent_name_set.add(parent.name)
                #     category_list.append({
                #         'id': category.id,
                #         "encrypted_id" : parent.encrypted_id,
                #         'name': parent.name,
                #         'image': parent.image.url if parent.image else 'image not found',
                #         'slug': parent.name.lower().replace(' ', '-')
                #     })
            # data['categories']=category_list
                    
            
            return Response({'status':True,'data': data,'message':'Products successfully displayed'}, status=status.HTTP_200_OK)
        except Exception as e:  
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class WebProductListAPIView(APIView):
    pagination_class = WebProductPaginationClass

    def get(self, request, parent_slug, category_slug=None):
        matched_category = None

        # New query params (clean style)
        query = request.query_params.get('q')  # search
        price_range = request.query_params.get('price_range')
        order_by = request.query_params.get('order_by', 'low_to_high')  

        min_price, max_price = None, None
        if price_range:
            try:
                # Convert "[1000,3000]" -> [1000, 3000]
                price_range = price_range.strip("[]").split(",")
                min_price, max_price = float(price_range[0]), float(price_range[1])
            except Exception:
                pass

        # Category matching
        if category_slug:
            for category in CategoryModel.objects.filter(is_active=True):
                if slugify(category.name) == category_slug:
                    parent = category.get_parent()
                    if parent and slugify(parent.name) == parent_slug:
                        matched_category = category
                        break
        else:
            for category in CategoryModel.objects.filter(is_active=True):
                if slugify(category.name) == parent_slug:
                    matched_category = category
                    break

        if not matched_category:
            return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)

        # Product fetching
        if matched_category.is_root():
            descendants = matched_category.get_descendants()
            all_categories = [matched_category] + list(descendants)
            products = ProductModel.objects.filter(category__in=all_categories, is_published=True)
        else:
            products = ProductModel.objects.filter(category=matched_category, is_published=True)

        # Apply price filter with "discount first" logic
        if min_price is not None and max_price is not None:
            discounted_products = products.filter(
                product_price__isnull=False,
                product_price__range=(min_price, max_price)
            )

            if discounted_products.exists():
                products = discounted_products
            else:
                products = products.filter(
                    product_price__isnull=True,
                    product_price__range=(min_price, max_price)
                )

        # Apply search
        if query:
            products = products.filter(
                Q(name__icontains=query) |
                Q(category__name__icontains=query) |
                Q(description__icontains=query) |
                Q(care_instructions__icontains = query) |
                Q(delivery_information__icontains=query)
            )

        # Apply sorting
        if order_by == "low_to_high":
            products = products.order_by("product_price")
        elif order_by == "high_to_low":
            products = products.order_by("-product_price")
        else:  # newest default
            products = products.order_by("-created_at")

        # Pagination
        paginator = self.pagination_class()
        paginator.page_size = 12
        paginated_products = paginator.paginate_queryset(products, request)
        serializer = WebProductSerializer(paginated_products, many=True)

        return Response({
            "status": True,
            "data": serializer.data,
            "count": paginator.page.paginator.count,
            "total_pages": paginator.page.paginator.num_pages,
            "current_page": paginator.page.number,
            "next": paginator.get_next_link(),
            "previous": paginator.get_previous_link(),
        }, status=status.HTTP_200_OK)
