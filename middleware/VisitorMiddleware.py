class checkvisitorstatus:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        visitor_id = request.headers.get('visitor')
        if visitor_id is None:
            pass
        else:   
            try:
                from user_app.models import VisitorModel     
                from django.db.models import Count

                VisitorModel.objects.get_or_create(visitor_id=visitor_id)
            except VisitorModel.DoesNotExist:
                pass
            except VisitorModel.MultipleObjectsReturned:
                duplicates = (VisitorModel.objects
                    .values('visitor_id')
                    .annotate(count=Count('id'))
                    .filter(count__gt=1))
                for item in duplicates:
                    visitor_id = item['visitor_id']
                    objs = VisitorModel.objects.filter(visitor_id=visitor_id).order_by('id')
                    objs.exclude(id=objs.first().id).delete()

        response = self.get_response(request)
        return response