from rest_framework.response import Response
from rest_framework import status
from management_app.serializer.InventorySerializer import *
from ..models import *
from django.utils.text import slugify
from rest_framework.views import APIView
from django.db.models import Q
from ..pagination import ListPagination
from xhtml2pdf import pisa
from django.conf import settings
from django.template.loader import render_to_string
from django.http import HttpResponse

class MobileInventoryView(APIView):
    def get(self, request, id=None):
        try:
            # --- Query Params ---
            is_pdf = request.query_params.get("is_pdf", False)
            all_records = request.query_params.get("all", False)
            search = request.query_params.get("search", "").strip()

            # --- Single Inventory ---
            if id:
                inventories = Inventory.objects.filter(id=id)
                if not inventories.exists():
                    return Response(
                        {"status": False, "message": "Inventory not found"},
                        status=status.HTTP_404_NOT_FOUND,
                    )

                serializer = MobileInventorySerializer(inventories, many=True)
                data = serializer.data
                for item in data:
                    item["batch"] = 1

                # --- PDF Export ---
                if is_pdf in ["1", "true", "True", True]:
                    return self.generate_pdf(data,request)

                return Response(
                    {
                        "status": True,
                        "message": "Inventory retrieved successfully",
                        "data": data,
                    },
                    status=status.HTTP_200_OK,
                )

            # --- All Inventories ---
            inventories = Inventory.objects.all().order_by("-id")

            # Apply Search Filter
            if search:
                inventories = inventories.filter(
                    Q(product__name__icontains=search)
                    | Q(serialno__serial_no__icontains=search)
                )

            # Pagination Setup
            paginator = ListPagination()
            if all_records in ["1", "true", "True", True]:
                paginated_inventories = None
            else:
                paginated_inventories = paginator.paginate_queryset(inventories, request)

            # Serialize
            if paginated_inventories is not None:
                serializer = MobileInventorySerializer(paginated_inventories, many=True)
            else:
                serializer = MobileInventorySerializer(inventories, many=True)

            data = serializer.data
            for item in data:
                item["batch"] = 1
                
            # --- PDF Export Check BEFORE Pagination Response ---
            if is_pdf in ["1", "true", "True", True]:
                return self.generate_pdf(data,request)

            # Normal JSON Response
            if paginated_inventories is not None:
                return paginator.get_paginated_response(data)

            return Response(
                {
                    "status": True,
                    "message": "Inventory list retrieved successfully",
                    "data": data,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"status": False, "message": f"Error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def generate_pdf(self, data, request):
            """Render inventory data into a PDF file and return a download URL."""
            try:
                # --- Render HTML Template ---
                html_content = render_to_string(
                    "inventory_pdf_template.html",
                    {"inventories": data},
                )

                # --- Ensure export directory exists ---
                export_dir = os.path.join(settings.MEDIA_ROOT, "export", "inventory_pdf")
                os.makedirs(export_dir, exist_ok=True)

                # --- Generate unique PDF filename ---
                file_name = f'inventory_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
                file_path = os.path.join(export_dir, file_name)

                # --- Generate PDF ---
                with open(file_path, "wb") as pdf_file:
                    pisa_status = pisa.CreatePDF(html_content, dest=pdf_file)

                if pisa_status.err:
                    return Response(
                        {"status": False, "message": "Error generating PDF"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

                # --- Build absolute download URL ---
                file_uri = os.path.join(settings.MEDIA_URL, "export", "inventory_pdf", file_name)
                absolute_file_uri = request.build_absolute_uri(file_uri)

                # --- Return JSON with download URL ---
                return Response({
                    "status": True,
                    "file_uri": absolute_file_uri,
                    "message": "Inventory PDF successfully generated"
                }, status=status.HTTP_200_OK)

            except Exception as e:
                return Response(
                    {"status": False, "message": f"PDF Error: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )