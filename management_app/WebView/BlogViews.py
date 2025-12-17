from rest_framework import generics
from management_app.models import BlogModel
from management_app.serializers import BlogModelSerializer
from rest_framework.response import Response
from rest_framework import status


class BlogModelListView(generics.ListAPIView):
    serializer_class = BlogModelSerializer

    def get_queryset(self):   
        queryset = BlogModel.objects.filter(is_published=True).order_by('-published_at')
        return queryset

    def list(self, request, pk=None, *args, **kwargs):
        id = pk
        
        try:
            if id is not None:
                blog = BlogModel.objects.get(id=id)
                serializer = BlogModelSerializer(blog, context={'request': request})
                
                blogs = self.filter_queryset(self.get_queryset())
                
                next_post = blogs.filter(published_at__lt=blog.published_at).first()
                previous_post = blogs.filter(published_at__gt=blog.published_at).last()

                if not previous_post:           
                    previous_post = blogs.last()
                if not next_post:
                    next_post = blogs.first()
                    
                return Response({
                    'status': True, 
                    'data': serializer.data, 
                    'previousPost': {
                        'id': previous_post.id, 
                        'title': previous_post.title, 
                        'banner_url': str(request.build_absolute_uri(previous_post.banner.url))
                    } if previous_post else None,
                    'nextPost': {
                        'id': next_post.id, 
                        'title': next_post.title, 
                        'banner_url': str(request.build_absolute_uri(next_post.banner.url))
                    } if next_post else None,
                }, status=status.HTTP_200_OK)
            
            else:
                queryset = self.filter_queryset(self.get_queryset())
                serializer = self.get_serializer(queryset, many=True)
                response_data = {
                    'status': True,
                    'latest_blogs': serializer.data[:4],
                    'all_blogs': serializer.data,
                }
                return Response(response_data)
                
                
        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

