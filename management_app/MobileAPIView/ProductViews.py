from management_app.models import ProductModel
from rest_framework.views import APIView
from management_app.serializer.ProductSerializer import MobileProductSerializer
from rest_framework.response import Response
from rest_framework import status
from ..pagination import PostListPagination
from ..models import *
from django.db.models import Sum
from django.db.models import Q
from management_app.translator import get_lang_code

class GetProductAPI(APIView):
    def post(self, request):
        product_id = request.data.get('product_id')
        barcode_number = request.data.get('barcode_number')
        lang = get_lang_code(request)
        products = ProductModel.objects.all()
        
        if product_id:
            products = products.filter(id=product_id)

        elif barcode_number:
            products = products.filter(upc_barcode=barcode_number)

        else:
            return Response(
                {'status': False, 'error': 'Product ID or Barcode number is required'},
                status=status.HTTP_200_OK
            )

        if not products.exists():
            return Response(
                {'status': False, 'error': 'No product found'},
                status=status.HTTP_200_OK
            )

        serializer = MobileProductSerializer(products, many=True, context={"request": request, "lang": lang})
        return Response({
            'status': True,
            'data': serializer.data,
            'message': 'Product Detail Show Successfully'
        }, status=status.HTTP_200_OK)

class FilterProductAPI(APIView):
    pagination_class = PostListPagination
    def post(self, request):
        category_id = request.data.get('category_id')
        product_name = request.data.get('product_name')  
        from_price = request.data.get('from_price') 
        to_price = request.data.get('to_price')
        sort_by = request.data.get('sort_by')
        lang = get_lang_code(request)
 
        productes = ProductModel.objects.all().order_by('-id')

        if category_id:
            category_ids = [int(cid) for cid in category_id.split(',') if cid.strip().isdigit()]
            productes = productes.filter(category__in=category_ids)
            
        if product_name:
            productes = productes.filter(name__icontains=product_name)
            
        price_field = 'product_price' 

        user = getattr(request, 'user', None)
        if user and user.is_authenticated and user.role:
            role_type = user.role.type.lower() if user.role.type else ""
            if role_type == 'retailer':
                price_field = 'retailer_price'
            elif role_type == 'wholesaler':
                price_field = 'distributer_price'
            elif role_type == 'distributer':
                price_field = 'distributer_price'

        if from_price and to_price:
            filter_kwargs = {
                f"{price_field}__gte": from_price,
                f"{price_field}__lte": to_price
            }
            productes = productes.filter(**filter_kwargs)

        if sort_by == "high":
            productes = productes.order_by(f"-{price_field}")
        elif sort_by == "low":
            productes = productes.order_by(price_field)
        elif sort_by == "a_to_z":
            productes = productes.order_by("name")
        elif sort_by == "z_to_a":
            productes = productes.order_by("-name")

        paginator = self.pagination_class()
        all_records = request.data.get('all', False)

        if all_records and all_records in ['1', 'true', 'True', True]:
            serializer = MobileProductSerializer(productes, many=True, context={"request": request, "lang": lang})
            return Response({'status': True, 'message': 'List Product Successfully', 'brand_banner': '', 'data': serializer.data}, status=status.HTTP_200_OK)

        paginated_products = paginator.paginate_queryset(productes, request)
        serializer = MobileProductSerializer(paginated_products, many=True, context={"request": request, "lang": lang})
        return paginator.get_paginated_response(serializer.data)

class SubCategoryProductListAPI(APIView):
    pagination_class = PostListPagination
    def post(self, request):
        sub_category_id = request.data.get('sub_category_id')
        brand_id = request.data.get('brand_id')
        search = request.data.get('search')
        filter = request.data.get('filter')
        from_price = request.data.get('from_price')
        to_price = request.data.get('to_price')
        lang = get_lang_code(request)
        
        # if not sub_category_id and not brand_id and not search and not filter and not from_price and not to_price:
        products = ProductModel.objects.all().order_by('-id')
            
        if sub_category_id:
            products = products.filter(sub_category = sub_category_id)
        
        if brand_id:
            products = products.filter(brand_id = brand_id)
            
        if search:
            products = products.filter(name__icontains = search)
            
        price_field = 'product_price' 

        user = getattr(request, 'user', None)
        if user and user.is_authenticated and user.role:
            role_type = user.role.type.lower() if user.role.type else ""
            if role_type == 'retailer':
                price_field = 'retailer_price'
            elif role_type == 'wholesaler':
                price_field = 'distributer_price'
            elif role_type == 'distributer':
                price_field = 'distributer_price'

        if from_price and to_price:
            filter_kwargs = {
                f"{price_field}__gte": from_price,
                f"{price_field}__lte": to_price
            }
            products = products.filter(**filter_kwargs)

        if filter == "high":
            products = products.order_by(f"-{price_field}")
        elif filter == "low":
            products = products.order_by(price_field)
        elif filter == "a_to_z":
            products = products.order_by("name")
        elif filter == "z_to_a":
            products = products.order_by("-name")
            
        paginator = self.pagination_class()
        all_records = request.data.get('all', False)

        if all_records and all_records in ['1', 'true', 'True', True]:
            serializer = MobileProductSerializer(products, many=True, context={"request": request, "lang": lang})
            return Response({'status': True, 'message': 'List Product Successfully', 'brand_banner': '', 'data': serializer.data}, status=status.HTTP_200_OK)

        paginated_products = paginator.paginate_queryset(products, request)
        serializer = MobileProductSerializer(paginated_products, many=True, context={"request": request, "lang": lang})
        return paginator.get_paginated_response(serializer.data)
        
class AllProductAPI(APIView):
    pagination_class = PostListPagination
    def post(self, request):
            search_query = request.query_params.get("search", "").strip()
            lang = get_lang_code(request)

            products = ProductModel.objects.all().order_by('-id')
            if search_query:
                products = products.filter(
                    Q(name__icontains=search_query) |
                    Q(item_code__icontains=search_query)  |
                    Q(short_description__icontains=search_query)  | 
                    Q(upc_barcode__icontains=search_query)  | 
                    Q(description__icontains=search_query) 
                )

            paginator = self.pagination_class()
            all_records = request.data.get('all', False)

            if all_records and all_records in ['1', 'true', 'True', True]:
                paginated_products = None
            else:
                paginated_products = paginator.paginate_queryset(products, request)

            if paginated_products is not None:
                serializer = MobileProductSerializer(paginated_products, many=True, context={"request": request, "lang": lang})
                return paginator.get_paginated_response(serializer.data)
            
            serializer = MobileProductSerializer(products, many=True, context={"request": request, "lang": lang})

            return Response({
                'status': True,
                'message': "List Product Successfully",
                'data': serializer.data
            }, status=status.HTTP_200_OK)   

class MobileShowAllProductsView(APIView):
    pagination_class = PostListPagination
    def post(self, request):
        product_type = request.data.get('type') 
        limit = request.data.get('limit','20')
        lang = get_lang_code(request)

        products = ProductModel.objects.all().order_by('-id')

        if product_type == 'latest_products':
            products = ProductModel.objects.order_by('-id')[:int(limit)]
            
        if product_type == 'popular_products':
            products = (
                ProductModel.objects
                .annotate(total_sold=Sum('orderlinesmodel__quantity'))
                .filter(total_sold__gt=0)
                .order_by('-total_sold')
            )
            
        if product_type == 'best_selling':
            products = (
                ProductModel.objects
                .annotate(total_sold=Sum('orderlinesmodel__quantity'))
                .filter(total_sold__gt=0)
                .order_by('-total_sold')
            )
            
        if product_type == 'limited_stock_offers':
            products = ProductModel.objects.filter(limited_stock="Yes").order_by('-id')
            
        if product_type == 'out_of_stock':
            products = ProductModel.objects.filter(out_of_stock="Yes").order_by('-id')
            
        # else:
        #     return Response({'status': False, 'message': 'Invalid product type'}, status=status.HTTP_400_BAD_REQUEST)

        if limit:
            try:
                limit = int(limit)
                products = products[:limit]
            except ValueError:
                pass
                
        paginator = self.pagination_class()
        all_records = request.data.get('all', False)

        if all_records and all_records in ['1', 'true', 'True', True]:
            serializer = MobileProductSerializer(products, many=True, context={"request": request, "lang": lang})
            return Response({
                'status': True,
                'message': f'{product_type.replace("_"," ").title()} Products List',
                'data': serializer.data,
            }, status=status.HTTP_200_OK)

        paginated_products = paginator.paginate_queryset(products, request)
        serializer = MobileProductSerializer(paginated_products, many=True, context={"request": request, "lang": lang})
        return paginator.get_paginated_response(serializer.data)