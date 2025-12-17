from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class ErpPaginationWithPageCount(PageNumberPagination):
    page_size_query_param = 'page_size'  # Optional: allow ?page_size=20
    max_page_size = 100  # Optional limit
 
    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'status': True,
            'data': data
        })


class WebProductPaginationClass(ErpPaginationWithPageCount):
    page_size = 48
    max_page_size = 25
    page_query_param = 'page'    

    def get_page_size(self, request):
        # Override get_page_size to allow dynamic setting based on query parameters
        page_size = super().get_page_size(request)
        if 'row_per_page' in request.query_params:
            page_size = int(request.query_params['row_per_page'])
        return page_size
    
    
class ProductPagination(ErpPaginationWithPageCount):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 50

    def get_page_size(self, request):
        # Override get_page_size to allow dynamic setting based on query parameters
        page_size = super().get_page_size(request)
        if 'row_per_page' in request.query_params:
            page_size = int(request.query_params['row_per_page'])
        return page_size
