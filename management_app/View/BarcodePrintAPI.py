from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import HttpResponse
from management_app.models import ProductModel


def generate_single_tspl(item_code, short_desc, price, barcode):
    big_price = f"1{int(price)}2"

    return f"""
SIZE 38 mm, 15 mm
GAP 3 mm
DIRECTION 1
REFERENCE 0,0
CLS

TEXT 15,5,"2",0,1,1,"{item_code}"
TEXT 255,5,"2",0,1,1,"{short_desc}"

TEXT 125,27,"2",0,1,1,"{big_price}"

BARCODE 25,52,"128",28,1,0,2,2,"{barcode}"

PRINT 1
"""


def build_tspl(products, qty):
    final = ""

    for p in products:
        item_code = p.item_code or ""
        short_desc = p.short_description or ""
        price = p.product_price or p.retailer_price or 0
        barcode = p.upc_barcode

        for i in range(qty):
            final += generate_single_tspl(item_code, short_desc, price, barcode)

    return final

class BarcodeTSPLDownloadAPIView(APIView):

    def post(self, request):
        ids = request.data.get("ids", [])
        qty = int(request.data.get("qty", 1))
        products = ProductModel.objects.filter(id__in=ids)
        tspl = build_tspl(products, qty)
        return Response({"status": True, "message": "Barcodes sent to USB printer", "tspl": tspl})
