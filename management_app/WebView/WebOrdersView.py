from rest_framework.response import Response
from rest_framework import status
from management_app.models import OrderLinesModel, OrderModel
from management_app.paginations import WebProductPaginationClass
from rest_framework.filters import SearchFilter
from rest_framework.views import APIView
from management_app.serializer.WebOrderSerializer import WebOrderSerializer
from django_filters.rest_framework import DjangoFilterBackend
from management_app.translator import translate_text as t
from management_app.translator import get_lang_code

class WebOrderView(APIView):
    pagination_class = WebProductPaginationClass
    filter_backends = (DjangoFilterBackend, SearchFilter)

    
    def get(self,request,id=None):
        user = request.user
        lang = get_lang_code(request)
        
        if id:
            try:
                order = OrderLinesModel.objects.get(id=id, order__customer=user)
                serializer = WebOrderSerializer(order, context={'request': request, 'lang': lang})
                return Response({
                    "status": True,
                    "data": serializer.data,
                    "message": t("Order details retrieved successfully.", lang)
                }, status=status.HTTP_200_OK)
            
            except OrderLinesModel.DoesNotExist:
                return Response({
                    "status": False,
                    "message": t("Wrong Order", lang)
                }, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({
                    "status": False,
                    "message": t(str(e), lang)
                }, status=status.HTTP_400_BAD_REQUEST)
                
                
        orders = OrderLinesModel.objects.filter(order__customer=user).order_by('-order__created_at')
        paginator = self.pagination_class()
        paginated_orders = paginator.paginate_queryset(orders, request)
        serializer=WebOrderSerializer(paginated_orders,many=True,context={'request': request, 'lang' :lang})
        return Response({
            'status':True,
            'data':serializer.data,
            'count':orders.count(),
            'total_pages':paginator.page.paginator.num_pages,
            "message": t("Successfully retrieved data", lang)
        },status=status.HTTP_200_OK)