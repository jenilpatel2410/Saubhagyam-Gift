from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from user_app.models import VisitorModel
from management_app.serializer.CartSerializer import WebCartSerializer
from management_app.models import ProductModel, Cart
from django.db.models import Sum
from management_app.translator import translate_text as t
from management_app.translator import get_lang_code


def all_total_counters(request):
    visitor_id = request.headers['Visitor'] if "Visitor" in request.headers.keys() else None
    if visitor_id:
        visitor_user = VisitorModel.objects.filter(visitor_id=visitor_id).first()
        cart_items = Cart.objects.filter(visitor__id=visitor_user.id)
    else:
        cart_items = Cart.objects.filter(user__id=request.user.id)
        
    sub_total = 0
    # discount_amt = 0
    if not len(cart_items) == 0:
        sub_total = sum([item.total_price for item in cart_items])
        # discount_amt = sum([item.total for item in cart_items])
    
    final_total = (sub_total - 0) if sub_total > 0 else 0

    all_totals = {
        "total": round(sub_total, 2), 
        "discount_amt": 0, #discount_amt,
        "gst_amt": 0, #round(gst_amt, 2), 
        "final_total": round(final_total, 2)
    }
    return all_totals


# def cart_counter(request):
#     try:
#         visitor_id= request.headers['Visitor'] if "Visitor" in request.headers.keys() else None
#         if visitor_id:
#             visitor_user = VisitorModel.objects.filter(visitor_id=visitor_id).first()
#             count_cart = Cart.objects.filter(visitor__id=visitor_user.id)
#         else:
#             count_cart = Cart.objects.filter(user__id=request.user.id)

#         distinct_products_quantity = count_cart.values('product').annotate(total_quantity=Sum('quantity'))

#         total_products_count = sum(item['total_quantity'] for item in distinct_products_quantity)
#         return total_products_count
#     except Exception as e:
#         err =str(e)
#         return Response({'status':False,'error':f'{err}'}, status=status.HTTP_200_OK)
def cart_counter(request):
    try:
        visitor_id = request.headers['Visitor'] if "Visitor" in request.headers.keys() else None
        if visitor_id:
            visitor_user = VisitorModel.objects.filter(visitor_id=visitor_id).first()
            count_cart = Cart.objects.filter(visitor__id=visitor_user.id)
        else:
            count_cart = Cart.objects.filter(user__id=request.user.id)

        distinct_products_quantity = count_cart.values('product').annotate(total_quantity=Sum('qty'))

        total_products_count = sum(item['total_quantity'] for item in distinct_products_quantity)
        return total_products_count
    except Exception as e:
        # instead of Response, return a safe default value
        return 0
    
class CartAPI(APIView):

    def get(self, request):
        cart_id = request.query_params.get("cart_id")  # check if cart_id is passed
        lang = get_lang_code(request)

        visitor_id = request.headers['Visitor'] if "Visitor" in request.headers.keys() else None
        get_user_token = request.headers['Authorization'].split()[-1] if "Authorization" in request.headers.keys() else None

        if cart_id:
            cart_items = Cart.objects.filter(id=cart_id)

            if cart_items.exists():
                serializer = WebCartSerializer(cart_items,many=True, context={'request': request, 'lang' : lang})
                total = sum([item.total_price for item in cart_items])
                # counter = sum([item.quantity for item in cart_items])  # count quantity only for this cart_id

                return Response(
                    {
                        'status': True,
                        'data': {
                            'cart_items': serializer.data,
                            'cart_counter': cart_counter(request),
                            "total": total,
                            "discount_amt": 0,
                            "gst_amt": 0,
                            "final_total": total
                        },
                        'message': t("Cart successfully displayed", lang)
                    },
                    status=status.HTTP_200_OK
                )

            return Response(
                {
                    'status': True,
                    'data': {
                        'cart_counter': 0,
                        "total": 0,
                        "discount_amt": 0,
                        "gst_amt": 0,
                        "final_total": 0
                    },
                    'message': t("Cart not found", lang)
                },
                status=status.HTTP_200_OK
            )

        else:
            if get_user_token is not None:
                cart_items = Cart.objects.filter(user__id=request.user.id).order_by('id')
            elif visitor_id is not None:
                visitor_user = VisitorModel.objects.filter(visitor_id=visitor_id).first()
                cart_items = Cart.objects.filter(visitor__id=visitor_user.id).order_by('id')
            else:
                cart_items = []

            if cart_items:
                serializer = WebCartSerializer(cart_items, many=True, context={'request': request, 'lang':lang})
                return Response(
                    {
                        'status': True,
                        'data': {
                            'cart_items': serializer.data,
                            'cart_counter': cart_counter(request),
                            **all_total_counters(request)
                        },
                        'message': t("Cart successfully displayed", lang)
                    },
                    status=status.HTTP_200_OK
                )

            return Response(
                {
                    'status': True,
                    'data': {
                        'cart_counter': 0,
                        **all_total_counters(request)
                    },
                    'message': t("Your cart is empty", lang)
                },
                status=status.HTTP_200_OK
            )

    def post(self, request):
        
        visitor_id = request.headers['Visitor'] if "Visitor" in request.headers.keys() else None
        user_id = request.headers['Authorization'] if "Authorization" in request.headers.keys() else None
        pid = request.data.get('pid')
        qty = request.data.get('quantity')
        lang = get_lang_code(request)
        
        if not pid or not qty:
            return Response({'status': False, 'error': t('Product and Quantity', lang)}, status=status.HTTP_400_BAD_REQUEST) 
        
        if visitor_id is not None and user_id is None:
            try:
                visitor_user = VisitorModel.objects.filter(visitor_id=visitor_id).first()                    
                product = ProductModel.objects.get(id=pid)
                
                if not Cart.objects.filter(visitor__id=visitor_user.id, product__id=request.data['pid']).exists():
                    cart_data = {
                        'visitor': visitor_user.id,
                        'product': product.id,
                        'qty': int(qty) or 1,
                    }

                    serializer = WebCartSerializer(data=cart_data, context={'request': request, 'lang': lang})

                    if serializer.is_valid():
                        serializer.save()
                        return Response({'status': True, 'data': serializer.data, 'cart_counter': cart_counter(request), 'message': t(f"{product.name} Added successfully in cart", lang)}, status=status.HTTP_201_CREATED)
                    else:
                        return Response({'status': False, 'error': t(serializer.errors, lang)}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    product = ProductModel.objects.get(id=pid)
                    cart_data = Cart.objects.get(visitor__id=visitor_user.id, product__id=request.data['pid'])

                    cart_data.qty += int(qty) or 1
                    cart_data.save()
                    serializer = WebCartSerializer(cart_data, context={'request': request, 'lang': lang})

                    return Response({'status': True, 'data': serializer.data, 'cart_counter': cart_counter(request), 'message': t(f"{product.name} Added successfully in cart", lang)}, status=status.HTTP_201_CREATED)

            except Exception as e:
                err = str(e)
                return Response({'status': False, 'error': f'{err}'}, status=status.HTTP_200_OK)
        else:
            try:
                product = ProductModel.objects.get(id=pid)
                if not Cart.objects.filter(user__id=request.user.id, product__id=request.data['pid']).exists():
                    cart_data = {
                        'user': request.user.id,
                        'product': product.id,
                        'qty': int(qty) or 1,
                    }

                    serializer = WebCartSerializer(data=cart_data, context={'request': request, 'lang': lang})
                    if serializer.is_valid():
                        serializer.save()
                        return Response({'status': True, 'data': serializer.data, 'cart_counter': cart_counter(request), 'message': t(f"{product.name} Added successfully in cart", lang)}, status=status.HTTP_201_CREATED)
                    else:
                        return Response({'status': False, 'error': t(serializer.errors, lang)}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    product = ProductModel.objects.get(id=pid)
                    cart_data = Cart.objects.get(user__id=request.user.id, product__id=request.data['pid'])

                    cart_data.qty += int(qty) or 1
                    cart_data.save()
                    serializer = WebCartSerializer(cart_data, context={'request': request, 'lang': lang})

                    return Response({'status': True, 'data': serializer.data, 'cart_counter': cart_counter(request), 'message': t(f"{product.name} Added successfully in cart", lang)}, status=status.HTTP_201_CREATED)

            except Exception as e:
                err = str(e)
                return Response({'status': False, 'error': t(f'{err}', lang)}, status=status.HTTP_200_OK)

    def patch(self,  request, pk=None, format=None):
        id = pk

        visitor_id = request.headers['Visitor'] if "Visitor" in request.headers.keys() else None
        lang = get_lang_code(request)
        
        if visitor_id is not None:
            try:
                visitor_user = VisitorModel.objects.filter(visitor_id=visitor_id).first()
                get_product = Cart.objects.get(visitor__id=visitor_user.id, id=id)
            except VisitorModel.DoesNotExist:
                return Response({'status': False, 'message': t("Unauthorized", lang)}, status=status.HTTP_401_UNAUTHORIZED)
            except Cart.DoesNotExist:
                return Response({'status': False, 'message': t("Cart item not found!", lang)}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                err = str(e)
                return Response({'status': False, 'error': t(err, lang)}, status=status.HTTP_200_OK)
        else:
            try:
                get_product = Cart.objects.get(user__id=request.user.id, id=id)
            except Exception as e:
                err = str(e)
                return Response({'status': False, 'error': t(f'{err}', lang)}, status=status.HTTP_200_OK)

        serializer = WebCartSerializer(get_product, data=request.data, partial=True, context={'request': request, 'lang' : lang})
        if serializer.is_valid():
            serializer.save()
            return Response({'status': True, "data": serializer.data, "cart_counter": cart_counter(request), **all_total_counters(request), 'message': t(f"{get_product.product.name} successfully updated", lang)}, status=status.HTTP_200_OK)
        else:
            return Response({'status': False, "errors": t(serializer.errors, lang)}, status=status.HTTP_200_OK)

    def delete(self, request, pk=None, format=None):
        id = pk
        if id is not None:
            try:
                visitor_id = request.headers['Visitor'] if "Visitor" in request.headers.keys() else None
                lang = get_lang_code(request)

                if visitor_id:
                    visitor_user = VisitorModel.objects.filter(visitor_id=visitor_id).first()
                    get_product = Cart.objects.get(visitor__id=visitor_user.id, id=id)
                    get_product.delete()
                else:
                    get_product = Cart.objects.get(user__id=request.user.id, id=id)
                    get_product.delete()
                return Response({'status': True, 'cart_counter': cart_counter(request), **all_total_counters(request), 'message': t('Cart sucessfully deleted', lang)}, status=status.HTTP_200_OK)
            except Exception as e:
                err = str(e)
                return Response({'status': False, 'error': t(f'{err}', lang)}, status=status.HTTP_200_OK)
        else:
            try:
                visitor_id = request.headers['Visitor'] if "Visitor" in request.headers.keys() else None
                if visitor_id:
                    visitor_user = VisitorModel.objects.filter(visitor_id=visitor_id).first()
                    get_product = Cart.objects.filter(visitor__id=visitor_user.id)
                    get_product.delete()
                else:
                    get_product = Cart.objects.filter(user__id=request.user.id)
                    get_product.delete()
                return Response({'status': True, 'cart_counter': cart_counter(request), **all_total_counters(request), 'message': t('Cart sucessfully deleted', lang)}, status=status.HTTP_200_OK)
            except Exception as e:
                err = str(e)
                return Response({'status': False, 'error': t(f'{err}', lang)}, status=status.HTTP_200_OK)


