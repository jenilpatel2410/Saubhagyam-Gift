from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from ..models import *
from ..serializer.BrandSerializer import MobileBrandSerializer
from ..serializer.OfferSerializer import MobileOfferSliderSerializer
from ..serializer.ProductSerializer import MobileDashboardProductSerializer
from ..serializer.CategorySerializer import MobileCategorySerializer
from django.db.models import Sum
from management_app.translator import get_lang_code

class MobileDashboardView(APIView):
    def post(self, request):
        
        user_id = request.data.get('user_id')
        lang = get_lang_code(request)
        
        # --- MULTILANGUAGE SECTION TITLES ---
        section_titles = {
            'latest_products': {
                'en': 'Latest Products',
                'hi': 'नवीनतम उत्पाद',
                'gu': 'નવીનતમ ઉત્પાદનો',
                'mr': 'नवीन उत्पादने',
                'bn': 'সর্বশেষ পণ্য',
                'ta': 'புதிய தயாரிப்புகள்',
                'te': 'తాజా ఉత్పత్తులు',
                'kn': 'ಹೊಸ ಉತ್ಪನ್ನಗಳು',
                'ml': 'പുതിയ ഉൽപ്പന്നങ്ങൾ',
                'pa': 'ਤਾਜ਼ਾ ਉਤਪਾਦ',
            },
            'popular_products': {
                'en': 'Popular Products',
                'hi': 'लोकप्रिय उत्पाद',
                'gu': 'લોકપ્રિય ઉત્પાદનો',
                'mr': 'लोकप्रिय उत्पादने',
                'bn': 'জনপ্রিয় পণ্য',
                'ta': 'பிரபலமான தயாரிப்புகள்',
                'te': 'ప్రముఖ ఉత్పత్తులు',
                'kn': 'ಜನಪ್ರಿಯ ಉತ್ಪನ್ನಗಳು',
                'ml': 'ജനപ്രിയ ഉൽപ്പന്നങ്ങൾ',
                'pa': 'ਲੋਕਪ੍ਰਿਯ ਉਤਪਾਦ',
            },
            'limited_stock_offers': {
                'en': 'Limited Stock Offers',
                'hi': 'सीमित स्टॉक ऑफर',
                'gu': 'મર્યાદિત સ્ટોક ઓફર્સ',
                'mr': 'मर्यादित स्टॉक ऑफर',
                'bn': 'সীমিত স্টক অফার',
                'ta': 'குறிப்பிட்ட கையிருப்பு சலுகைகள்',
                'te': 'పరిమిత స్టాక్ ఆఫర్లు',
                'kn': 'ಸೀಮಿತ ಸ್ಟಾಕ್ ಆಫರ್‌ಗಳು',
                'ml': 'പരിമിത സ്റ്റോക്ക് ഓഫറുകൾ',
                'pa': 'ਸੀਮਿਤ ਸਟਾਕ ਪੇਸ਼ਕਸ਼ਾਂ',
            },
            'out_of_stock': {
                'en': 'Out Of Stock',
                'hi': 'स्टॉक समाप्त',
                'gu': 'સ્ટોક સમાપ્ત',
                'mr': 'स्टॉक संपला',
                'bn': 'স্টক শেষ',
                'ta': 'பொருட்கள் இல்லை',
                'te': 'స్టాక్ అయిపోయింది',
                'kn': 'ಸ್ಟಾಕ್ ಮುಗಿದಿದೆ',
                'ml': 'സ്റ്റോക്ക് തീർന്നിരിക്കുന്നു',
                'pa': 'ਸਟਾਕ ਖਤਮ',
            },
            'best_selling': {
                'en': 'Best Selling',
                'hi': 'सबसे अधिक बिकने वाले उत्पाद',
                'gu': 'સૌથી વધુ વેચાતા ઉત્પાદનો',
                'mr': 'सर्वाधिक विक्री होणारी उत्पादने',
                'bn': 'সর্বাধিক বিক্রিত পণ্য',
                'ta': 'சிறந்த விற்பனையாளர் தயாரிப்புகள்',
                'te': 'అత్యధికంగా అమ్ముడయ్యే ఉత్పత్తులు',
                'kn': 'ಅತ್ಯಧಿಕವಾಗಿ ಮಾರಾಟವಾದ ಉತ್ಪನ್ನಗಳು',
                'ml': 'ഏറ്റവും കൂടുതൽ വിറ്റ ഉൽപ്പന്നങ്ങൾ',
                'pa': 'ਸਭ ਤੋਂ ਵੱਧ ਵਿਕਣ ਵਾਲੇ ਉਤਪਾਦ',
            },
        }

        # Helper function to fetch localized title
        def get_title(key):
            return section_titles.get(key, {}).get(lang, section_titles.get(key, {}).get('en'))
        
        category = CategoryModel.get_root_nodes().filter(is_active=True).order_by('id')
        offer_slider = OfferSliderModel.objects.order_by('-id')
        
        queryset = ProductModel.objects.all()
        
        latest_product = queryset.order_by('-id')[:5]
        popular_product = (
            queryset
            .annotate(total_sold=Sum('orderlinesmodel__quantity'))
            .filter(total_sold__gt=0)  
            .order_by('-total_sold')[:5]  
        )
        limited_products = queryset.filter(limited_stock="Yes").order_by('-id')[:5]
        out_of_stock = queryset.filter(out_of_stock='Yes').order_by('-id')[:5]
        best_selling_products = (
            queryset
            .annotate(total_sold=Sum('orderlinesmodel__quantity'))
            .filter(total_sold__gt=0)  
            .order_by('-total_sold')[:5]  
        )
        
        categoryserializer = MobileCategorySerializer(category, many=True, context={'request': request, 'lang': lang})
        offerSliderSerializer = MobileOfferSliderSerializer(offer_slider, many=True, context={'request': request, 'lang': lang})
        latestProductSerializer = MobileDashboardProductSerializer(latest_product, many=True, context={'request': request, 'lang': lang})
        popularProductSerializer = MobileDashboardProductSerializer(popular_product, many=True, context={'request': request, 'lang': lang})
        limitedProductSerializer = MobileDashboardProductSerializer(limited_products, many=True, context={'request': request, 'lang': lang})
        bestSellingSerializer = MobileDashboardProductSerializer(best_selling_products, many=True, context={'request': request, 'lang': lang})
        outOfStockSerializer = MobileDashboardProductSerializer(out_of_stock, many=True, context={'request': request, 'lang': lang})
        
        response_data = {
            'brand': categoryserializer.data if categoryserializer.data else [],
            'offer': offerSliderSerializer.data if offerSliderSerializer.data else [],
            'data1': []
        }

        # Add sections only if serializer has data
        if latestProductSerializer.data:
            response_data['data1'].append({
                'id': 1,
                'name': get_title('latest_products'),
                'key': 'latest_products',
                'children': latestProductSerializer.data,
            })

        if popularProductSerializer.data:
            response_data['data1'].append({
                'id': 2,
                'name': get_title('popular_products'),
                'key': 'popular_products',
                'children': popularProductSerializer.data,
            })

        if limitedProductSerializer.data:
            response_data['data1'].append({
                'id': 3,
                'name': get_title('limited_stock_offers'),
                'key': 'limited_stock_offers',
                'children': limitedProductSerializer.data,
            })

        if outOfStockSerializer.data:
            response_data['data1'].append({
                'id': 4,
                'name': get_title('out_of_stock'),
                'key': 'out_of_stock',
                'children': outOfStockSerializer.data,
            })

        if bestSellingSerializer.data:
            response_data['data1'].append({
                'id': 5,
                'name': get_title('best_selling'),
                'key': 'best_selling',
                'children': bestSellingSerializer.data,
            })

        return Response({
            'status': True,
            'message': 'List Products Successfully.',
            'data': response_data
        })
