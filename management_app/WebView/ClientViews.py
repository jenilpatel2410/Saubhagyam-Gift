from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..models import Client
from ..serializers import ClientSerializer
from management_app.translator import get_lang_code

class ClientListAPIView(APIView):
    def get(self, request):
        lang = get_lang_code(request)
        clients = Client.objects.filter(is_active=True).order_by('name')
        serializer = ClientSerializer(clients, many=True,context={'request':request,'lang': lang})
        return Response({'status': True,
                        'data': {'clients':serializer.data},
                        'message': "Clients successfully displayed"
                        }, 
                        status=status.HTTP_200_OK)
