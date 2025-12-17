from rest_framework.response import Response
from rest_framework import status
from management_app.serializer.WebProductSerializer import ProductDetailSerializer
from management_app.models import ProductModel
from django.db.models import Sum , Q
from django.shortcuts import get_object_or_404
from rest_framework.generics import RetrieveAPIView
import base64
from management_app.translator import get_lang_code


class WebProductDetailAPIView(RetrieveAPIView):
    serializer_class = ProductDetailSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['user'] = self.request.user
        return context

    def get_queryset(self):
        return ProductModel.objects.prefetch_related('product_tag').order_by('name')

    def get_object(self):
        """
        Decode the encrypted_id from the URL into the actual DB id.
        """
        encrypted_id = self.kwargs.get('id')  # URL param name
        try:
            decoded_id = int(base64.urlsafe_b64decode(encrypted_id.encode()).decode())
        except Exception:
            raise ValueError("Invalid product ID")

        return get_object_or_404(self.get_queryset(), id=decoded_id)

    def retrieve(self, request, *args, **kwargs):
        try:
            product = self.get_object()
            serializer = self.get_serializer(product, context={'request': request, 'lang': get_lang_code(request)})
            return Response({"status": True, 'data': serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            if str(e) == "Invalid product ID":
                return Response({"status": False, 'message': "Product Not Found"}, status=status.HTTP_404_NOT_FOUND)
            return Response({"status": False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        