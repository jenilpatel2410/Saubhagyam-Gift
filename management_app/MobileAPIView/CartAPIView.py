from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from ..models import Cart, UserModel, ProductModel, BrandModel
from management_app.serializer.CartSerializer import CartSerializer
from rest_framework.permissions import IsAuthenticated
from management_app.translator import get_lang_code

class GetCartAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, *args, **kwargs):
        user_id = request.data.get("user_id")
        lang = get_lang_code(request)

        if not user_id:
            return Response({
                "status": False,
                "message": "User ID is required",
                "errors": {"user_id": "This field is required"}
            }, status=status.HTTP_200_OK)

        user = UserModel.objects.filter(id=user_id).first()
        if not user:
            return Response({
                "status": False,
                "message": "User Not Found",
                "errors": "User Not Found"
            }, status=status.HTTP_400_BAD_REQUEST)

        carts = Cart.objects.filter(user=user, status=0)

        if not carts.exists():
            return Response({
                "status": False,
                "message": "Your cart is empty",
                "errors": "Data not found"
            }, status=status.HTTP_200_OK)
        serializer = CartSerializer(carts, many=True, context={"request": request,'lang': lang})

        return Response({
            "status": True,
            "message": "Cart fetched successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class AddToCartAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, *args, **kwargs):
        user_id = request.data.get("user_id")
        product_id = request.data.get("product_id")
        qty = request.data.get("qty", 1)
        discount = request.data.get('discount',0)
        
        if not user_id or not product_id or not qty:
            return Response({
                "status": False,
                "message": "All fields are required",
                "errors": "Provide All fields."
            }, status=status.HTTP_200_OK)

        # User check
        user = UserModel.objects.filter(id=user_id).first()
        if not user:
            return Response({
                "status": False,
                "message": "User Not Found",
                "errors": "User Not Found"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Product check
        product = ProductModel.objects.filter(id=product_id).first()
        if not product:
            return Response({
                "status": False,
                "message": "Product Not Found",
                "errors": "Product Not Found"
            }, status=status.HTTP_200_OK)

        # If cart item already exists → update qty
        cart_item, created = Cart.objects.get_or_create(
            user=user,
            product=product,
            defaults={"qty": qty,"discount":discount,}
        )
        if not created:
            cart_item.qty = int(qty)
            cart_item.discount = discount
            cart_item.save()

        serializer = CartSerializer(cart_item, context={"request": request})
        count = Cart.objects.filter(user=user).count()
        return Response({
            "status": True,
            "data": serializer.data,
            "count": count,
            "message": "Item added to cart successfully",
        }, status=status.HTTP_200_OK)

class UpdateCartAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, *args, **kwargs):
        user_id = request.data.get("user_id")
        product_id = request.data.get("product_id")
        qty = request.data.get("qty")
        discount = request.data.get('discount')

        if not user_id or not product_id or qty is None:
            return Response(
                {"error": "user_id, product_id and qty are required"},
                status=status.HTTP_200_OK
            )
            
        try:
            user = UserModel.objects.get(id=user_id)
            product = ProductModel.objects.get(id=product_id)
        except UserModel.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        except ProductModel.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            cart_item = Cart.objects.get(user=user, product=product)
            cart_item.qty = qty
            if discount:
                cart_item.discount = discount
            cart_item.save()

            serializer = CartSerializer(cart_item, context={"request": request})
            
            return Response(
                {
                    "status": True,
                    "data": serializer.data,
                    "message": "Cart updated successfully",
                },
                status=status.HTTP_200_OK
            )
        except Cart.DoesNotExist:
            return Response(
                {"status": False, "message": "Cart item not found for this user and product"},
                status=status.HTTP_200_OK
            )

class RemoveCartAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, *args, **kwargs):
        user_id = request.data.get("user_id")
        product_id = request.data.get("product_id")

        if not user_id or not product_id:
            return Response(
                {"error": "user_id and product_id are required"},
                status=status.HTTP_200_OK
            )

        try:
            cart_item = Cart.objects.get(user_id=user_id, product_id=product_id)
            cart_item.delete()
            
            count = Cart.objects.filter(user_id=user_id).count()

            return Response(
                {
                    "status": True,
                    "message": "Remove Product from Cart Successfully",
                    "count": count,
                },
                status=status.HTTP_200_OK,
            )
        except Cart.DoesNotExist:
            return Response(
                {
                    "status": False,
                    "message": "No Products In the cart",
                    "count": 0,
                },
                status=status.HTTP_200_OK, 
            )