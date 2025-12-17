# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from ..models import OrderModel, OrderLinesModel, ProductModel, BrandModel,Cart,OnlinePaymentsModel,Inventory
from django.utils import timezone
from user_app.models import UserModel
from ..serializer.OrderSerializer import  MobileOrderSerializer,MobileOrderLineSerializer, MobileOrderDetailSerializer
from rest_framework.permissions import IsAuthenticated
import json

class PlaceOrderView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        data = request.data.get("products", [])
        if not data:
            return Response({"status": False, "remark": "No products provided", "data": [], "message": "Failed"}, status=status.HTTP_200_OK)

        first_item = data[0]
        try:
            user = UserModel.objects.get(id=first_item.get("user_id"))
        except UserModel.DoesNotExist:
            return Response({
                'status': False,
                'message': 'User not found',
                'errors': 'Invalid user_id'
            }, status=status.HTTP_200_OK)

        brand = None
        brand_id = first_item.get("brand_id")
        if brand_id:
            try:
                brand = BrandModel.objects.get(id=brand_id)
            except BrandModel.DoesNotExist:
                pass

        # Create order
        order = OrderModel.objects.create(
            customer=user,
            brand_id=brand,
            product_info= data,
            shipping_address=first_item.get("shipping_address"),
            pay_type=first_item.get("payment_type"),
            transaction_id=first_item.get("transaction_id"),
            main_price=first_item.get("main_price") or 0,
            percentage_off=first_item.get("percentage_off") or 0,
            remark=first_item.get("remark", ""),
            final_total=sum([float(p.get("checkout_price", 0)) for p in data]),
            product_total=sum([float(p.get("total_price", 0)) for p in data]),
            sale_status = "Sales Order",
        )

        # Create order lines
        for p in data:
            product = ProductModel.objects.get(id=p.get("product_id"))
            
            if not product:
                return Response({
                    'status': False,
                    'message': f"Product with id {p.get('product_id')} not found"
                }, status=status.HTTP_200_OK)
                
            OrderLinesModel.objects.create(
                order=order,
                product=product,
                quantity=float(p.get("qty", 0)),
                selling_price=float(p.get("price", 0)),
                product_total=float(p.get("total_price", 0)),
            )
            
        # Remove cart items after order placed
        product_ids = [p.get("product_id") for p in data]
        Cart.objects.filter(user=user, product_id__in=product_ids).delete()

        # Get all order lines for this order
        lines = OrderLinesModel.objects.filter(order=order)
        serializer = MobileOrderLineSerializer(lines, many=True)

        return Response({
            "status": True,
            "remark": None,
            "data": serializer.data,
            "message": "Your Order Added Successfully"
        }, status=status.HTTP_200_OK)


class UserOrdersView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user_id = request.data.get("user_id")

        if not user_id:
            return Response(
                {"status": False, "message": "user_id is required"},
                status=status.HTTP_200_OK,
            )

        user = UserModel.objects.get(id=user_id)
        
        if not user:
            return Response({
                'status': False,
                'message': 'User not found'
            }, status= status.HTTP_200_OK)

        orders = OrderModel.objects.filter(customer=user).order_by("-id")

        serializer = MobileOrderSerializer(orders, many=True)

        return Response(
            {
                "status": True,
                "message": "List Order Successfully",
                "data": serializer.data
            },
            status=status.HTTP_200_OK,
        )

from management_app.translator import get_lang_code

class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]
    def post (self, request):
        lang = get_lang_code(request)
        user_id = request.data.get("user_id")
        order_number = request.data.get("order_number")
        
        if not user_id:
            return Response({
                'status': False,
                'message': 'user_id is required'
            }, status= status.HTTP_200_OK)
            
        if not order_number:
            return Response({
                'status': False,
                'message': 'order_number is required'
            }, status= status.HTTP_200_OK)
        
        try:
            user = UserModel.objects.get(id=user_id)
        except UserModel.DoesNotExist:
            return Response({
                'status': False,
                'message': 'User not found'
            }, status=status.HTTP_200_OK)

        try:
            order = OrderModel.objects.get(order_id=order_number)
        except OrderModel.DoesNotExist:
            return Response({
                'status': False,
                'message': 'Order not found'
            }, status=status.HTTP_200_OK)

        serializer = MobileOrderDetailSerializer(order, context={"order_id": order_number,"request": request,'lang': lang})
        return Response({
            "status": True,
            "message": "List Order Details Successfully",
            **serializer.data
        }, status=status.HTTP_200_OK)
        
class MobileCustomerPlaceOrderView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user_id = request.data.get('user_id')
        customer_id = request.data.get('customer_id')
        is_draft = request.data.get('is_draft', False)
        order_from_admin = request.data.get('order_from_admin', False)
        paid_amount_str = request.data.get('paid_amount')
        
        try:
            paid_amount = float(paid_amount_str) if paid_amount_str not in [None, ''] else 0.00
        except ValueError:
            paid_amount = 0.00
        
        if is_draft and is_draft in ['1', 'true', 'True', True]:
            is_draft = True
        else:
            is_draft = False
        
        if not user_id and not customer_id:
            return Response({
                'status':False,
                'message': 'user_id and customer_id required.'
            })
        
        try:
            user = UserModel.objects.get(id=user_id)
        except UserModel.DoesNotExist:
            return Response({
                'status': False,
                'message': 'User not found',
                'errors': 'Invalid user_id'
            }, status=status.HTTP_200_OK)
            
        try:
            customer = UserModel.objects.get(id=customer_id)
        except Exception as e:
            customer = UserModel.objects.filter(role__type='Admin').first()
            # return Response({
            #     'status': False,
            #     'message': 'Customer not found',
            #     'errors': 'Invalid customer_id'
            # }, status=status.HTTP_200_OK)

        cart_items = Cart.objects.filter(user=user)
        if not cart_items.exists():
            return Response({
                "status": False,
                "message": "No items in cart",
                "data": []
            }, status=status.HTTP_200_OK)

        final_total = sum([item.discount_price * item.qty for item in cart_items])
        product_total = sum([item.price * item.qty for item in cart_items])
        
        final_total = float(final_total)
        paid_amount = float(paid_amount)

        order_advance = 0.0   # new advance created by this order
        order_balance = 0.0   # new balance (unpaid) created by this order
        is_paid = False

        is_admin_order = (str(order_from_admin).lower() == 'true' or order_from_admin is True)

        if is_admin_order:
            old_unpaid = float(customer.unpaid_amount or 0.0)
            old_advance = float(customer.advance_amount or 0.0)

            # 🔹 CASE 1: Paid >= Current Order
            if paid_amount >= final_total:
                extra = paid_amount - final_total  # after clearing current order
                order_balance = 0.0

                if extra > 0:
                    # Use extra to clear old unpaid
                    if extra >= old_unpaid:
                        extra -= old_unpaid
                        old_unpaid = 0.0

                        # if any old advance exists, use it to clear nothing, so it stays
                        # leftover extra becomes new advance
                        order_advance = extra
                        is_paid = True
                    else:
                        # Extra partially clears old unpaid
                        old_unpaid -= extra

                        # Now check if old_advance can clear remaining unpaid
                        if old_advance > 0:
                            if old_advance >= old_unpaid:
                                old_advance -= old_unpaid
                                old_unpaid = 0.0
                                is_paid = True
                            else:
                                old_unpaid -= old_advance
                                old_advance = 0.0
                                is_paid = False
                        else:
                            is_paid = False

                        order_advance = 0.0
                        order_balance = old_unpaid
                else:
                    # Paid exactly equals final total → check if old advance/unpaid affects status
                    order_advance = 0.0
                    order_balance = old_unpaid
                    is_paid = (old_unpaid == 0)

                # Update user record
                customer.advance_amount = old_advance + order_advance
                customer.unpaid_amount = old_unpaid
                customer.save()

            # 🔹 CASE 2: Paid < Current Order
            else:
                remaining_due = final_total - paid_amount

                # Try to use old advance to cover remaining_due
                if old_advance >= remaining_due:
                    old_advance -= remaining_due
                    remaining_due = 0.0
                    order_balance = 0.0
                    is_paid = True
                    # old unpaid remains as-is
                    customer.unpaid_amount = old_unpaid
                    customer.advance_amount = old_advance
                else:
                    # Advance insufficient — unpaid increases
                    remaining_due -= old_advance
                    old_advance = 0.0
                    order_balance = old_unpaid + remaining_due
                    is_paid = False
                    customer.unpaid_amount = order_balance
                    customer.advance_amount = 0.0

                order_advance = 0.0
                customer.save()
                
        # Get address instance safely
        if str(order_from_admin).lower() in ['true', '1', 'yes'] or order_from_admin is True:
            address_qs = getattr(customer, "address", None)
        else:
            address_qs = getattr(user, "address", None)

        # Ensure it's a queryset, not None
        customer_address_instance = address_qs.first() if address_qs and hasattr(address_qs, "first") else None

        # Build address string
        if customer_address_instance:
            customer_address_str = (
                f"{customer_address_instance.street or ''}, "
                f"{customer_address_instance.address or ''}, "
                f"{customer_address_instance.landmark or ''}, "
                f"{customer_address_instance.city or ''}, "
                f"{customer_address_instance.state or ''}, "
                f"{customer_address_instance.country or ''}, "
                f"{customer_address_instance.pincode or ''}"
            ).strip(', ')
        else:
            customer_address_str = ""
            
        # Create the order
        order = OrderModel.objects.create(
            sales_person=user if str(order_from_admin).lower() == 'true' or order_from_admin == True else customer,
            customer=customer if str(order_from_admin).lower() == 'true' or order_from_admin == True else user,
            brand_id=None,
            product_info=json.dumps([{
                "product_id": item.product.id,
                "name": item.product.name,
                "qty": item.qty,
                "price": float(item.price),
                "discount": float(item.discount),
                "discount_price": float(item.discount_price),
            } for item in cart_items]),
            shipping_address= customer_address_str if str(order_from_admin).lower() == 'true' or order_from_admin == True else request.data.get("shipping_address"),
            pay_type=request.data.get("payment_type"),
            transaction_id=request.data.get("transaction_id"),
            main_price=product_total,
            percentage_off=0,
            remark=request.data.get("remark", ""),
            final_total=final_total,
            product_total=product_total,
            sale_status="Sales Order",
            order_status="delivered" if (str(order_from_admin).lower() == 'true' or order_from_admin == True) and not is_draft else "pending",
            advance_amount = float(order_advance),
            balance_amount = float(order_balance),
            paid_amount = float(paid_amount),
            is_paid = is_paid,
            is_draft = is_draft,
        )
        
        pay_type = str(request.data.get("payment_type", "")).lower()
        if pay_type == "online":
            OnlinePaymentsModel.objects.create(
                txn_id=request.data.get("transaction_id"),
                order_id=order,
                user=user,
                status=True,  # You can set False if pending verification
                payment_datetime=timezone.now(),
                amount=final_total,
                payment_mode=request.data.get("mode"),
            )

        # 4️⃣ Create order lines
        for cart_item in cart_items:
            line_total = cart_item.discount_price * cart_item.qty
            OrderLinesModel.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.qty,
                selling_price=cart_item.price,
                discount=cart_item.discount,
                discount_price=cart_item.discount_price,
                product_total=line_total,
            )
            
        cart_items.delete()

        # Serialize order lines
        lines = OrderLinesModel.objects.filter(order=order)
        serializer = MobileOrderLineSerializer(lines, many=True)

        return Response({
            "status": True,
            "data": serializer.data,
            "message": "Order placed successfully"
        }, status=status.HTTP_200_OK)
        
class RecievedOrderStatusChange(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        order_id = request.data.get('order_id')
        order_status = request.data.get('status')
        if not order_id:
            return Response({
                'status': False,
                'message': 'order_id is required'
            }, status=status.HTTP_200_OK)
        
        try:
            order = OrderModel.objects.get(id=order_id)
        except OrderModel.DoesNotExist:
            return Response({
                'status': False,
                'message': 'Order not found'
            }, status=status.HTTP_200_OK)
            
        if order_status:
            order.order_status = order_status
            order.save()
        
        return Response({
            'status': True,
            'message': 'Order status updated to received'
        }, status=status.HTTP_200_OK)

class MobileUpdateOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        order_id = request.data.get('order_id')
        is_draft = request.data.get('is_draft')
        order_from_admin = request.data.get('order_from_admin', False)
        paid_amount_str = request.data.get('paid_amount')
        
        try:
            paid_amount = float(paid_amount_str) if paid_amount_str not in [None, ''] else 0.00
        except ValueError:
            paid_amount = 0.00
        
        if not order_id:
            return Response({
                'status': False,
                'message': 'order_id is required.'
            }, status=status.HTTP_200_OK)

        try:
            order = OrderModel.objects.get(id=order_id)
        except OrderModel.DoesNotExist:
            return Response({
                'status': False,
                'message': 'Order not found.'
            }, status=status.HTTP_200_OK)
            
        if not order.is_draft:
            return Response({
                'status': False,
                'message': 'This order is not in draft mode, so it cannot be updated.'
            }, status=status.HTTP_200_OK)
            
        if is_draft and is_draft in ['1', 'true', 'True', True]:
            is_draft = True
        else:
            is_draft = False

        user = order.sales_person
        customer = order.customer
        is_admin_order = str(order_from_admin).lower() in ['true', '1', 'yes']

        # ------------------ Recalculate Totals ------------------
        order_lines = OrderLinesModel.objects.filter(order=order)
        main_total = sum(float(line.selling_price or 0) * float(line.quantity or 0) for line in order_lines)
        final_total = sum(float(line.discount_price or 0) * float(line.quantity or 0) for line in order_lines)

        order.main_price = main_total
        order.product_total = final_total
        order.final_total = final_total

        # ------------------ Admin Logic for Advance/Unpaid ------------------
        old_unpaid = float(customer.unpaid_amount or 0.0)
        old_advance = float(customer.advance_amount or 0.0)

        order_advance = 0.0
        order_balance = 0.0
        is_paid = False

        if is_admin_order:
            old_unpaid = float(customer.unpaid_amount or 0.0)
            old_advance = float(customer.advance_amount or 0.0)

            # 🔹 CASE 1: Paid >= Current Order
            if paid_amount >= final_total:
                extra = paid_amount - final_total  # after clearing current order
                order_balance = 0.0

                if extra > 0:
                    # Use extra to clear old unpaid
                    if extra >= old_unpaid:
                        extra -= old_unpaid
                        old_unpaid = 0.0

                        # if any old advance exists, use it to clear nothing, so it stays
                        # leftover extra becomes new advance
                        order_advance = extra
                        is_paid = True
                    else:
                        # Extra partially clears old unpaid
                        old_unpaid -= extra

                        # Now check if old_advance can clear remaining unpaid
                        if old_advance > 0:
                            if old_advance >= old_unpaid:
                                old_advance -= old_unpaid
                                old_unpaid = 0.0
                                is_paid = True
                            else:
                                old_unpaid -= old_advance
                                old_advance = 0.0
                                is_paid = False
                        else:
                            is_paid = False

                        order_advance = 0.0
                        order_balance = old_unpaid
                else:
                    # Paid exactly equals final total → check if old advance/unpaid affects status
                    order_advance = 0.0
                    order_balance = old_unpaid
                    is_paid = (old_unpaid == 0)

                # Update user record
                customer.advance_amount = old_advance + order_advance
                customer.unpaid_amount = old_unpaid
                customer.save()

            # 🔹 CASE 2: Paid < Current Order
            else:
                remaining_due = final_total - paid_amount

                # Try to use old advance to cover remaining_due
                if old_advance >= remaining_due:
                    old_advance -= remaining_due
                    remaining_due = 0.0
                    order_balance = 0.0
                    is_paid = True
                    # old unpaid remains as-is
                    customer.unpaid_amount = old_unpaid
                    customer.advance_amount = old_advance
                else:
                    # Advance insufficient — unpaid increases
                    remaining_due -= old_advance
                    old_advance = 0.0
                    order_balance = old_unpaid + remaining_due
                    is_paid = False
                    customer.unpaid_amount = order_balance
                    customer.advance_amount = 0.0

                order_advance = 0.0
                customer.save()
        
        # Get address instance safely
        if str(order_from_admin).lower() in ['true', '1', 'yes'] or order_from_admin is True:
            address_qs = getattr(user, "address", None)
        else:
            address_qs = getattr(customer, "address", None)

        # Ensure it's a queryset, not None
        customer_address_instance = address_qs.first() if address_qs and hasattr(address_qs, "first") else None

        # Build address string
        if customer_address_instance:
            customer_address_str = (
                f"{customer_address_instance.street or ''}, "
                f"{customer_address_instance.address or ''}, "
                f"{customer_address_instance.landmark or ''}, "
                f"{customer_address_instance.city or ''}, "
                f"{customer_address_instance.state or ''}, "
                f"{customer_address_instance.country or ''}, "
                f"{customer_address_instance.pincode or ''}"
            ).strip(', ')
        else:
            customer_address_str = ""
            
        # ------------------ Update Order ------------------
        order.shipping_address= customer_address_str if str(order_from_admin).lower() == 'true' or order_from_admin == True else request.data.get("shipping_address")
        order.pay_type=request.data.get("payment_type")
        order.transaction_id=request.data.get("transaction_id")
        order.remark=request.data.get("remark", "")
        order.advance_amount = float(order_advance)
        order.balance_amount = float(order_balance)
        order.paid_amount = float(order.paid_amount or 0.0) + paid_amount
        order.is_paid = is_paid
        order.is_draft = is_draft
        order.order_status = "delivered" if (str(order_from_admin).lower() == 'true' or order_from_admin == True) and not is_draft else "pending"
        # Update product_info field
        product_info_data = [{
            "product_id": line.product.id if line.product else None,
            "name": line.product.name if line.product else "",
            "qty": float(line.quantity or 0),
            "price": float(line.selling_price or 0),
            "discount": float(line.discount or 0),
            "discount_price": float(line.discount_price or 0),
        } for line in order_lines]

        order.product_info = json.dumps(product_info_data)
        order.save()

        # ------------------ Return Response ------------------
        serializer = MobileOrderLineSerializer(order_lines, many=True)
        return Response({
            "status": True,
            "message": "Order updated successfully",
            "data": {
                "order_id": order.id,
                "final_total": order.final_total,
                "paid_amount": order.paid_amount,
                "balance_amount": order.balance_amount,
                "advance_amount": order.advance_amount,
                "is_paid": order.is_paid,
                "lines": serializer.data
            }
        }, status=status.HTTP_200_OK)
