from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from management_app.models import Cart
from user_app.models import AddressModel, UserModel
from management_app.serializer.WebOrderSerializer import PlaceOrderSerializer
from django.db import transaction
from datetime import datetime, timedelta
from management_app.translator import translate_text as t
from management_app.translator import get_lang_code


class PlaceOrderAPI(APIView):
    @transaction.atomic
    def post(self, request):
        lang = get_lang_code(request)
        try:
            user = request.user 
            if not user.is_authenticated:
                return Response({"status": False, "error": t("You are not authorised to Place Order.", lang)}, status=status.HTTP_400_BAD_REQUEST)
            
            payment_type = request.data.get("payment_type")
            address_id = request.data.get("address_id")
            cart_id = request.data.get("cart_id")

            if payment_type != "Cash on Delivery":
                return Response({"status": False, "message": t("Not a valid Payment Method", lang)}, status=status.HTTP_400_BAD_REQUEST)

            # Get Address
            try:
                address_instance = AddressModel.objects.get(id=address_id)
                address_instance.is_default = True
                address_instance.save()
            except AddressModel.DoesNotExist:
                return Response({"status": False, "error": t("Address not found.", lang)}, status=status.HTTP_400_BAD_REQUEST)

            # Get Cart Items
            if cart_id:
                cart_items = Cart.objects.filter(id=cart_id, user=user)
            else:
                cart_items = Cart.objects.filter(user=user)

            if not cart_items.exists():
                return Response({"status": False, "error": t("Cart is empty.", lang)}, status=status.HTTP_400_BAD_REQUEST)

            # Totals
            total = sum(item.total_price for item in cart_items)
            # total_discount = sum(
            #     (item.product.base_price - item.product.discount_price) * item.quantity
            #     for item in cart_items if item.product.discount_price
            # )
            contact_instance = UserModel.objects.get(id=user.id)

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

            # Prepare serializer data
            serializer_data = {
                "customer": contact_instance.id,
                "address": address_instance.id,
                "shipping_address": address_instance.__str__(),
                "pay_type": "cod",
                "order_status": "pending",
                "final_total": float(total),
                "product_info": product_info_data,
                "product_total": float(total),
                # "product_total": float(total) + float(total_discount),
                # "discount_amt": float(total_discount),
                "is_ecommerce": True,
                'expiration_date': (datetime.now() + timedelta(days=10)).now(),
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
                "balance_amount": float(total),
            }

            serializer = PlaceOrderSerializer(data=serializer_data, context={'request': request, 'lang' : lang})
            serializer.is_valid(raise_exception=True)
            order = serializer.save()

            cart_items.delete()

            return Response({
                "status": True,
                "message": t("Order created successfully.", lang),
                "order_id": order.id,
                "unique_id": order.order_id,
                "total_price": order.final_total,
                "total_products": sum(item["quantity"] for item in serializer_data["order_lines"]),
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            transaction.set_rollback(True)
            return Response({"status": False, "error": t(str(e), lang)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
