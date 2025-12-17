from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from ..models import NewsModel
from ..serializer.NewsSerializer import MobileNewsModelSerializer

class NewsView(APIView):   
    def post(self, request):
        
        try:
            news = NewsModel.objects.all().order_by('-created_at')  
            serializer = MobileNewsModelSerializer(news, many=True)       
            return Response({
                "status": True,
                "message": "News fetched successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": False,
                "message": "Something went wrong",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)