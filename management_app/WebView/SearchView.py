import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Q
from ..models import ProductModel, CategoryModel,ProductTranslation
from management_app.serializer.WebProductSerializer import WebProductSerializer
from management_app.paginations import ProductPagination
import base64
from management_app.translator import get_lang_code

class ProductSearchAPIView(APIView):
    def get(self, request):
        query = request.GET.get('q', '').strip()
        price_range = request.GET.get('price_range')  
        order_by = request.GET.get('order_by')
        category_param = request.GET.get('category')
        lang = get_lang_code(request)        

        products = ProductModel.objects.filter(is_published=True)
        
        category = None
        if category_param and category_param.lower() != "all": 
            try:
                decoded_id = int(base64.urlsafe_b64decode(category_param.encode()).decode())
                category = get_object_or_404(CategoryModel, id=decoded_id)
            except Exception:
                return Response({
                    "status": False,
                    "message": "Invalid category ID"
                }, status=status.HTTP_400_BAD_REQUEST)

        if category:
            descendants = list(category.get_descendants())
            categories = [category] + descendants
            products = products.filter(
                Q(category__in=categories) | Q(sub_category__in=categories)
            )
            
        # Filter by search query
        # if query:
        #     products = products.filter(
        #         Q(name__icontains=query)
        #         # Q(category__name__icontains=query) |
        #         # Q(description__icontains=query) |
        #         # Q(care_instructions__icontains=query) |
        #         # Q(delivery_information__icontains=query) |
        #         # Q(metatitle__icontains=query) |
        #         # Q(metakeywords__icontains=query)
        #     )
        
        # 🔍 Multilingual Search
        if query:
            if lang and lang.lower() != "en":
                # Search in translation table for the selected language
                translated_product_ids = ProductTranslation.objects.filter(
                    language_code=lang,
                ).filter(
                    Q(name__icontains=query) |
                    Q(short_name__icontains=query) |
                    Q(description__icontains=query)
                ).values_list('product_id', flat=True)

                products = products.filter(
                    Q(id__in=translated_product_ids) |
                    Q(name__icontains=query)
                ).distinct()
            else:
                # English/default search
                products = products.filter(
                    Q(name__icontains=query) |
                    Q(short_name__icontains=query)
                )

        # Handle price_range using split
        min_price, max_price = None, None
        if price_range:
            try:
                price_range = price_range.strip("[]").split("-")
                if len(price_range) == 2:
                    min_price = float(price_range[0].strip())
                    max_price = float(price_range[1].strip())
            except Exception:
                pass  # ignore if parsing fails

        price_field = "retailer_price" 

        if request and hasattr(request, "user") and hasattr(request.user, "role") and hasattr(request.user.role, "type"):
            role_type = request.user.role.type
            if role_type == "Retailer":
                price_field = "retailer_price"
            elif role_type == "Wholesaler":
                price_field = "wholesaler_price"
            elif role_type == "Distributer":
                price_field = "distributer_price"

        # Filtering
        if min_price is not None and max_price is not None:
            discounted_products = products.filter(
                **{
                    f"{price_field}__isnull": False,
                    f"{price_field}__gte": min_price,
                    f"{price_field}__lte": max_price,
                }
            )
            if discounted_products.exists():
                products = discounted_products
            else:
                products = products.filter(
                    **{
                        f"{price_field}__isnull": True,
                        f"{price_field}__gte": min_price,
                        f"{price_field}__lte": max_price,
                    }
                )

        # Sorting
        if order_by == "low_to_high":
            products = products.order_by(price_field)
        elif order_by == "high_to_low":
            products = products.order_by(f"-{price_field}")
        else:  # newest default
            products = products.order_by("-created_at")

        # Pagination
        paginator = ProductPagination()
        paginated_products = paginator.paginate_queryset(products, request)
        serializer = WebProductSerializer(paginated_products, many=True,context={'lang': lang, 'request': request})

        return Response({
            "status": True,
            "products": serializer.data,
            "count": paginator.page.paginator.count,
            "total_pages": paginator.page.paginator.num_pages,
            "current_page": paginator.page.number,
            "next": paginator.get_next_link(),
            "previous": paginator.get_previous_link(),
        }, status=status.HTTP_200_OK)

