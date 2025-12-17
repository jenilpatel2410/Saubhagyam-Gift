from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from management_app.models import OrderLinesModel,OrderModel
from management_app.serializer.OrderSerializer import MobileOrderLineCreateUpdateSerializer,MobileOrderSerializer

class MobileOrderLineView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        order_id = request.query_params.get("order_id")

        if not order_id:
            return Response({
                'status': False,
                'message': "Order Id is required."
            }, status=status.HTTP_200_OK)
            
        try:
            order = OrderModel.objects.get(id=order_id)
        except OrderModel.DoesNotExist:
            return Response({
                'status': False,
                'message': "Order not found."
            }, status=status.HTTP_200_OK)

        if pk:
            try:
                order_line = OrderLinesModel.objects.get(pk=pk)
                serializer = MobileOrderLineCreateUpdateSerializer(order_line, context={'request': request})
                order_serializer = MobileOrderSerializer(order)
                return Response({
                    'status': True,
                    'message': 'Order Line Details Fetched Successfully.',
                    'order_line_data': serializer.data,
                    'order_detail': order_serializer.data
                }, status=status.HTTP_200_OK)
            except OrderLinesModel.DoesNotExist:
                return Response({
                    "status": False,
                    "error": "Order line not found"
                }, status=status.HTTP_200_OK)

        order_lines = OrderLinesModel.objects.filter(order__id=order_id).order_by('-id')
        serializer = MobileOrderLineCreateUpdateSerializer(order_lines, many=True, context={'request': request})
        order_serializer = MobileOrderSerializer(order)
        return Response({
            'status': True,
            'message': 'Order lines Fetched Successfully.',
            'order_line_data': serializer.data,
            'order_detail': order_serializer.data
        }, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = MobileOrderLineCreateUpdateSerializer(data=request.data,context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": True,
                "message": "Order line added successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        return Response({
            "status": False,
            "error": serializer.errors
        }, status=status.HTTP_200_OK)

    def patch(self, request, pk=None):
        if not pk:
            return Response({
                "status": False,
                "error": "Order line ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            order_line = OrderLinesModel.objects.get(pk=pk)
        except OrderLinesModel.DoesNotExist:
            return Response({
                "status":False,
                "error": "Order line not found"}, status=status.HTTP_200_OK)

        serializer = MobileOrderLineCreateUpdateSerializer(order_line, data=request.data, partial=True,context={'request': request} )
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status":True,
                "message": "Order updated successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        return Response({
            "status":False,
            "error":serializer.errors}, status=status.HTTP_200_OK)

    def delete(self, request, pk=None):
        if not pk:
            return Response({
                "status":False,
                "error": "Order line ID is required"}, status=status.HTTP_200_OK)

        try:
            order_line = OrderLinesModel.objects.get(pk=pk)
        except OrderLinesModel.DoesNotExist:
            return Response({
                "status":False,
                "error": "Order line not found"}, status=status.HTTP_200_OK)

        order = order_line.order
        order_line.delete()

        # Recalculate totals after deletion
        serializer = MobileOrderLineCreateUpdateSerializer()
        serializer.update_order_totals(order)

        return Response({
            "status":True,
            "message": "Order line deleted successfully"}, status=status.HTTP_200_OK)
