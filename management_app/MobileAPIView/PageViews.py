from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from ..models import PageModel
from ..serializer.PageModelSerializer import PageModelSerializer
from management_app.translator import get_lang_code

class PageView(APIView):
    def post(self, request):
        lang = get_lang_code(request)
        type = request.data.get('type')
        
        if not type:
            return Response({
                'status': False,
                'message': "Please enter valid Type ",
                'error': 'type is required'
            }, status = status.HTTP_200_OK)
            
        try: 
            if type:
                page = PageModel.objects.get(type=type)
            
            serializer = PageModelSerializer(page, context={'lang': lang})
            
            return Response({
                'status' : True,
                'message' : "Data fetch Successfully",
                'data' : serializer.data
            }, status = status.HTTP_200_OK)
            
        except PageModel.DoesNotExist:
           return Response({
               'status': False,
               'message': 'Records Are Not Found In Database',
               'error': "Records Are Not Found In Database"
           }, status= status.HTTP_404_NOT_FOUND) 
           