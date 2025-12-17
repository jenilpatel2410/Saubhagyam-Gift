# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..models import OnlinePaymentOfferModel
from ..serializer.OfferSerializer import MobileOnlinePaymentOfferSerializer

class OnlinePaymentOfferList(APIView):
    def post(self, request):
        offers = OnlinePaymentOfferModel.objects.all()
        serializer = MobileOnlinePaymentOfferSerializer(offers, many=True)
        return Response({
            "status": True,
            "message": "List Online Payment Offer Successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
