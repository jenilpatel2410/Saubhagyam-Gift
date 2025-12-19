from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..models import Cart, OnlinePaymentsModel
from user_app.models import UserModel, AddressModel
from ..serializer.WebOrderSerializer import PlaceOrderSerializer
from django.db import transaction
from datetime import datetime, timedelta
from management_app.translator import translate_text as t
from management_app.translator import get_lang_code

class OnlinePlaceOrderAPI(APIView):
    renderer_classes = [TemplateHTMLRenderer]  # Enable template rendering
 
    @transaction.atomic
    def post(self, request):
        lang = get_lang_code(request)
        try:
            payment_source = request.data.get("payment_source")
            payment_mode = request.data.get("mode")
            paid_online = payment_source == "payu"
            address_id = request.data.get("address1")
            payment_id = request.data.get('mihpayid')
            transaction_id = request.data.get('txnid')
            final_total = float(request.data.get('amount')) if request.data.get('amount') else 0
            payment_status = request.data.get('status')
            user_id = request.data.get('udf1')
            cart_id = request.data.get('udf5')
                
            if paid_online != True:
                return Response(
                    {"error": t("Invalid Payment Source", lang)},
                    template_name='order_success_fail.html',
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
            
            if payment_status == "failure":
                OnlinePaymentsModel.objects.create(
                    txn_id=transaction_id,
                    user=UserModel.objects.get(id=user_id),
                    status=False,
                    payment_datetime=datetime.strptime(
                        request.data.get('addedon'), '%Y-%m-%d %H:%M:%S').astimezone(),
                    amount=final_total,
                    payment_mode = payment_mode,
                )
                my_context_data = {
                    'pay_status': request.data.get('status'),
                    'transaction_id': transaction_id,
                }
            
            elif payment_status == "success":
                user = UserModel.objects.get(id=user_id)
                
                # customer = UserModel.objects.filter(role="Customer", id=user_id).first()
                
                customer_billing_address = AddressModel.objects.get(id=address_id)
                
                # Get Cart Items
                if cart_id:
                    cart_items = Cart.objects.filter(id=cart_id)
                else:
                    cart_items = Cart.objects.filter(user=user)
                
                # total_discount = sum(
                #     (item.product.base_price - item.product.discount_price) * item.quantity
                #     for item in cart_items if item.product.discount_price
                # )
                
                product_info_data = [
                    {
                        "product_id": item.product.id,
                        "product_name": item.product.name,
                        "quantity": item.qty,
                        "unit_price": float(item.price),
                        "total_price": float(item.total_price),
                    }
                    for item in cart_items
                ]
                
                serializer_data = {
                    "customer": user.id,
                    "address": customer_billing_address.id,
                    "shipping_address": customer_billing_address.__str__(),
                    "pay_type": "online",
                    "order_status": "pending",
                    "final_total": float(final_total),
                    "product_info": product_info_data,
                    "product_total": float(final_total),
                    # "product_total": float(final_total) + float(total_discount),
                    # "discount_amt": float(total_discount),
                    "is_ecommerce": True,
                    'payment_id': payment_id,
                    'transaction_id': transaction_id,
                    'expiration_date': (datetime.now() + timedelta(days=10)).now(),
                    'is_paid': True,
                    "order_lines": [
                        {
                            "product": item.product.id,
                            "quantity": item.qty,
                            "selling_price": item.price,
                            "product_total": item.total_price
                        }
                        for item in cart_items
                    ],
                    "sale_status" : "Sales Order",
                    "paid_amount": float(final_total),
                }
                
                serializer = PlaceOrderSerializer(data=serializer_data, context={'request': request})
                
                if serializer.is_valid():
                    order_data = serializer.save()
                    
                    OnlinePaymentsModel.objects.create(
                        txn_id=transaction_id,
                        order_id=order_data,
                        user=user,
                        status=True,
                        payment_datetime=datetime.strptime(
                            request.data.get('addedon'), '%Y-%m-%d %H:%M:%S').astimezone(),
                        amount=final_total,
                        payment_mode = payment_mode,
                    )
                    
                    cart_items.delete()
                    
                    my_context_data = {
                        'pay_status': request.data.get('status'),
                        'order_id': order_data.order_id,
                        'transaction_id': order_data.transaction_id,
                        'final_total': order_data.final_total,
                    }
                                        
                else:
                    my_context_data = {
                        'pay_status': request.data.get('status'),
                        'transaction_id': transaction_id,
                    }
                    
            else:
                my_context_data = {
                    'pay_status': request.data.get('status'),
                    'transaction_id': transaction_id,
                }
                
            return Response(my_context_data, template_name='order_success_fail.html', status=status.HTTP_200_OK)
        
        except Exception as e:
            transaction.set_rollback(True)
            print(e)
            return Response(
                {"error": str(e)},
                template_name='order_success_fail.html',
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except UserModel.DoesNotExist:
            return Response({'status': False, 'message': t("Invalid user ID!", lang)}, status=status.HTTP_400_BAD_REQUEST)
        except AddressModel.DoesNotExist:
            return Response({'status': False, 'message': t("Invalid addresses!", lang)}, status=status.HTTP_400_BAD_REQUEST)