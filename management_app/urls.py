from django.urls import path,include
from management_app.View.CategoryAPI import *
from management_app.View.ProductAPI import *
from management_app.View.BrandAPI import *
from management_app.View.BusinessCategoryAPI import *
from management_app.View.NewsAPI import *
from management_app.View.RoleAPI import *
from management_app.View.OfferAPIs import *
from management_app.View.InquiryAPI import *
from management_app.View.FeebackAPI import *
from management_app.View.OrderAPI import *
from management_app.View.DashboardAPIs import *
from management_app.View.CompanyAPI import *
from management_app.View.PurchaseOrderAPI import *
from management_app.View.VendorAPI import *
from management_app.View.InventoryAPI import *
from management_app.View.FeaturePermissionsAPIs import *
from management_app.View.BarcodePrintAPI import BarcodeTSPLDownloadAPIView
from management_app.View.Sales_forcastview import SalesForecastAPIView

from .views import *


from management_app.MobileAPIView.CartAPIView import GetCartAPIView,AddToCartAPIView,UpdateCartAPIView,RemoveCartAPIView
from management_app.MobileAPIView.CategoryAPIView import *
from management_app.MobileAPIView.InquiryAPIView import *
from management_app.MobileAPIView.VersionCheckAPIView import *
from management_app.MobileAPIView.HomeAPIView import *
from management_app.MobileAPIView.FavouriteViews import AddFavouriteAPI, RemoveFavouriteAPI, ListFavouriteAPI
from management_app.MobileAPIView.ProductViews import GetProductAPI, FilterProductAPI, SubCategoryProductListAPI, AllProductAPI,MobileShowAllProductsView
from management_app.MobileAPIView.OrderAPIView import PlaceOrderView, UserOrdersView, OrderDetailView, MobileCustomerPlaceOrderView, RecievedOrderStatusChange,MobileUpdateOrderView
from management_app.MobileAPIView.OnlinePaymentOfferView import OnlinePaymentOfferList
from management_app.MobileAPIView.NewsViews import NewsView
from management_app.MobileAPIView.PageViews import PageView
from management_app.MobileAPIView.DashboardAPIView import MobileDashboardView
from management_app.MobileAPIView.SalesView import *
from management_app.MobileAPIView.PurchseAPIView import *
from management_app.MobileAPIView.ReportsView import *
from management_app.MobileAPIView.InventoryAPIView import MobileInventoryView
from management_app.MobileAPIView.OrderLineAPIView import MobileOrderLineView

from management_app.WebView.WebCategoryView import WebCategoryListAPI
from management_app.WebView.WebProductView import WebHomeProductView
from management_app.WebView.SearchView import ProductSearchAPIView
from management_app.WebView.WebProductDetailView import WebProductDetailAPIView
from management_app.WebView.CartViews import CartAPI
from management_app.WebView.WebOrdersView import WebOrderView
from django.views.decorators.csrf import csrf_exempt
from management_app.WebView.PlaceOrderViews import PlaceOrderAPI
from management_app.WebView.BlogViews import BlogModelListView
from management_app.WebView.ClientViews import ClientListAPIView
from management_app.WebView.OrderPaymentLinkView import GetOrderPaymentLinkAPI
from management_app.WebView.OnlinePlaceOrderView import OnlinePlaceOrderAPI

urlpatterns = [

    # Admin Panel API  

    path('dashboard-stats/',DashboardView.as_view(),name='dashboard-stats'),
    path('dashboard-graph/',GraphView.as_view(),name='dashboard-graph'),
    
    path('categories/',CategoryAPI.as_view(),name='categories'),
    path('categories/<int:id>/',CategoryAPI.as_view(),name='categories'),
    path('categories/excel/',Export_categories_excel.as_view(),name='categories-excel'),

    path('home-categories/',HomeCategoryView.as_view(),name='home-categories'),

    path('sub-categories/',SubCategoryAPI.as_view(),name='sub-categories'),
    path('sub-categories/<int:id>/',SubCategoryAPI.as_view(),name='sub-categories'),
    path('sub-categories/excel/',Export_sub_categories_excel.as_view(),name='sub-categories-excel'),

    path('units/', UnitView.as_view(), name='units'),
    path('products/',ProductAPI.as_view(),name='products'),
    path('products/<int:id>/',ProductAPI.as_view(),name='products'),
    
    path('products/excel/',ProductExportView.as_view(),name='products-excel'),
    path('products/import-excel/', ProductExcelImportAPI.as_view(), name='product-import-excel'),
    path('products/barcode-download-pdf/',BarcodeDownloadPdfView.as_view(),name='products-barcode-pdf'),
    path('products/barcode-download-excel/',BarcodeDownloadExcelView.as_view(),name='products-barcode-excel'),

    path('orders/',OrderView.as_view(),name='orders'),
    path('order-details/<int:id>/',OrderDetailsView.as_view(),name='order-details'),
    path('order-details/pdf/',Order_Pdf_View.as_view(),name='order-details-pdf'),
    path('orders/excel/',Export_orders_excel.as_view(),name='orders-excel'),
    path('order/create/',OrderCreateAPI.as_view(), name='order-create'),
    path('order/update/<int:id>/',OrderCreateAPI.as_view(), name='order-update'),
    path('order/latest_id/', LatestOrderReferenceNoAPI.as_view(), name='order-create'),

    path('brands/',BrandAPI.as_view(),name='brands'),
    path('brands/<int:id>/',BrandAPI.as_view(),name='brands'),
    path('brands/csv/',Export_brand_csv.as_view(),name='brands'),
    path('brands/excel/',Export_brand_excel.as_view(),name='brands'),

    path('business-category/',BusinessCategoryAPI.as_view(),name='business-category'),
    path('business-category/<int:id>/',BusinessCategoryAPI.as_view(),name='business-category'),
    path('business-category/csv/',Export_business_categories_csv.as_view(),name='business-category-csv'),
    path('business-category/excel/',Export_business_categories_excel.as_view(),name='business-category-excel'),
    
    path('news/',NewsAPI.as_view(),name='news'),
    path('news/<int:id>/',NewsAPI.as_view(),name='news'),
    path('news/excel/',Export_news_excel.as_view(),name='news-excel'),

    path('roles/',RoleAPI.as_view(),name='roles'),
    path('roles/<int:id>/',RoleAPI.as_view(),name='roles'),
    path('roles/excel/',Export_role_excel.as_view(),name='roles-excel'),

    path('company/',ComapanyView.as_view(),name='company'),
    path('company/<int:id>/',ComapanyView.as_view(),name='company'),
    path('company/excel/',Export_companies_excel.as_view(),name='company-excel'),
    
    path('offers/',OfferView.as_view(),name='offers'),
    path('offers/<int:id>/',OfferView.as_view(),name='offers'),
    path('offers/excel/',Export_offers_excel.as_view(),name='offers-excel'),

    path('online-offers/',OnlinePaymentOfferView.as_view(),name='online-offers'),
    path('online-offers/<int:id>/',OnlinePaymentOfferView.as_view(),name='online-offers'),
    path('online-offers/excel/',Export_online_offers_excel.as_view(),name='online-offers-excel'),

    path('offer-slider/',OfferSliderView.as_view(),name='offer-slider'),
    path('offer-slider/<int:id>/',OfferSliderView.as_view(),name='offer_slider'),
    path('offer-slider/excel/',Export_offer_slider_image_excel.as_view(),name='offer-slider'),

    path('inquiries/',InquiryView.as_view(),name='inquiries'),
    path('inquiries/<int:id>/',InquiryView.as_view(),name='inquiries'),
    path('inquiries/excel/',Export_inquiry_excel.as_view(),name='inquiries-excel'),

    path('feedbacks/',FeedbackView.as_view(),name='feedbacks'),
    path('feedbacks/<int:id>/',FeedbackView.as_view(),name='feedbacks'),
    path('feedbacks/excel/',Export_feedback_excel.as_view(),name='feedbacks-excel'),
    


    path('vendor/',VendorView.as_view(),name='vendor'),
    path('vendor/<int:id>/',VendorView.as_view(),name='vendor'),
    path('vendor/excel/',Export_vendors_excel.as_view(),name='vendor-excel'),

    path('purchase-order/',PurchaseOrderView.as_view(),name='purchae-order'),
    path('purchase-order/<int:id>/',PurchaseOrderView.as_view(),name='purchae-order'),
    path('purchase-order/excel/',Export_purchase_orders_excel.as_view(),name='purchae-order-excel'),

    path('purchase-order-item/',PurchaseOrderItemView.as_view(),name='purchae-order-item'),
    path('purchase-items-import/',ImportPurchaseItemsView.as_view(),name='purchase-items-import'),
    path('purchase-order-item/<int:id>/',PurchaseOrderItemView.as_view(),name='purchae-order-item'),

    path('inventory/',InventoryView.as_view(),name='inventory'),
    path('inventory/<int:id>/',InventoryView.as_view(),name='inventory'),
    path('inventory/excel/',InventoryExcelView.as_view(),name='inventory-excel'),
    path('inventory/report/',InventoryReportView.as_view(),name='inventory-report'),

    path('feature-permissions/',FeaturePermissionView.as_view(),name='feature-permissions'),
    path('feature-permissions/<int:id>/',FeaturePermissionView.as_view(),name='feature-permissions'),

    path("api/barcodes-tspl/", BarcodeTSPLDownloadAPIView.as_view()),

    # path('serial-no/',SerialNoView.as_view(),name='serial-no'),
    # path('serial-no/<int:id>/',SerialNoView.as_view(),name='serial-no'),

    # path('countries/',CountryView.as_view(),name='countries'),
  
    #mobile api
    path('mobile/list-product/', SubCategoryProductListAPI.as_view(), name='subcategoryproduct-api'),
    path('mobile/list-product-detail/', GetProductAPI.as_view(), name='getproduct-api'),
    path('mobile/all_brand_product_filter/', FilterProductAPI.as_view(), name='filterproduct-api'),
    path('mobile/view-all-product/', AllProductAPI.as_view(), name='all-products'),
    path('mobile/search-products/', FilterProductAPI.as_view(), name='search-products'),
    path('mobile/show-all-products/', MobileShowAllProductsView.as_view(), name='mobile-show-all-products'),
    
    path('mobile/category/',CategoryList.as_view(),name='category'),
    path('mobile/sub-category/',SubCategoryList.as_view(),name='category'),
    
    path('mobile/cart-list/', GetCartAPIView.as_view(), name='cart-list'),
    path('mobile/add-to-cart/', AddToCartAPIView.as_view(), name='add-to-cart'),
    path('mobile/update-cart/', UpdateCartAPIView.as_view(), name='update-cart'),
    path('mobile/remove-cart/', RemoveCartAPIView.as_view(), name='remove-cart'),
  
    path('mobile/add-favourite/', AddFavouriteAPI.as_view(), name='add-favourite'),
    path('mobile/un-favourite/', RemoveFavouriteAPI.as_view(), name='remove-favourite'),
    path('mobile/list-favourite/', ListFavouriteAPI.as_view(), name='list-favourite'),
    
    path('mobile/add-place-order/', PlaceOrderView.as_view(), name='place-order'),
    path('mobile/customer-place-order/', MobileCustomerPlaceOrderView.as_view(), name='customer-place-order'),
    path('mobile/list-product-order/', UserOrdersView.as_view(), name='user-orders'),
    path('mobile/details-product-order/', OrderDetailView.as_view(), name='order-detail'),
    path('mobile/recieved-order-status-change/', RecievedOrderStatusChange.as_view(), name='recieved-order-status-change'),
    
    path('mobile/online-payment-offer-list/', OnlinePaymentOfferList.as_view(), name='online-payment-offer-list'),
  
    path('mobile/product-inquiry/',InquiryList.as_view(),name='category'),
    path('mobile/version-check/',VersionList.as_view(),name='category'),
    path('mobile/home/',HomeList.as_view(),name='home'),
    path('mobile/dashboard-view/', MobileDashboardView.as_view(), name='dashboard-view'),

    path('mobile/news-list/', NewsView.as_view(), name='news-list'),
    path('mobile/aboutus-privacy-terms/', PageView.as_view(), name='pages'),
    
    path('mobile/sales-invoice/',SalesView.as_view(),name='sales-invoice'),
    path('mobile/sales-invoice/<int:id>/',SalesView.as_view(),name='sales-invoice'),
    path('mobile/group-by-sales/',GroupBySalesView.as_view(),name='group-by-sales'),

    # path('mobile/sales-invoice/pdf/',SalesInvoicePDFView.as_view(),name='sales-invoice'),

     
    path('mobile/purchase-invoice/',PurchaseInvoiceView.as_view(),name='purchase-invoice'),
    path('mobile/purchase-invoice/<int:id>/',PurchaseInvoiceView.as_view(),name='purchase-invoice'),
    path('mobile/group-by-purchase/',GroupByPurchaseView.as_view(),name='group-by-purchase'),

    path('mobile/customer-report/',CustomerSalesReportView.as_view(),name='customer-report'),
    path('mobile/purchase-report/',PurchaseReportView.as_view(),name='purchase-report'),
    path('mobile/accounts-receivable-report/',AccountsReceivableReportView.as_view(),name='accounts-receivable-report'),
    path('mobile/accounts-payable-report/',AccountsPayableReportView.as_view(),name='accounts-payable-report'),
    path('mobile/high-value-customers/',HighValueCustomerView.as_view(),name='high-value-customers'),


    
    path('mobile/inventory/',MobileInventoryView.as_view(),name='inventory'),
    path('mobile/inventory/<int:id>/',MobileInventoryView.as_view(),name='inventory'),
    
    path("mobile/orderline/", MobileOrderLineView.as_view(), name="mobile_orderline_list_create"),
    path("mobile/orderline/<int:pk>/", MobileOrderLineView.as_view(), name="mobile_orderline_detail"),
    path("mobile/final-place-order/", MobileUpdateOrderView.as_view(), name="final-place-order"),
    
    #web api
    path("web/api/categories/", WebCategoryListAPI.as_view(), name="category-list"),
    path('web/products/home/', WebHomeProductView.as_view(), name='home_products'),
    path('search-products/', ProductSearchAPIView.as_view(), name='product_search_by_category'),
    path('web/product/<str:id>/', WebProductDetailAPIView.as_view(), name='products-details'),
    path('cart/', CartAPI.as_view(), name='cart'),
    path('cart/<int:pk>/', CartAPI.as_view(), name='cart'),
    path('web/orders/list/',WebOrderView.as_view(),name='web_orders_list'),
    path('web/order/list/<int:id>/',WebOrderView.as_view(),name='web-order-detail'),
    path('placeorder/', csrf_exempt(PlaceOrderAPI.as_view()), name='orderDisplay'),
    path('blogs/', BlogModelListView.as_view(), name='home-blogs'),
    path('blogs/<int:pk>/', BlogModelListView.as_view(), name='home-blogs'),
    path('clients/', ClientListAPIView.as_view(), name='client-list'),
    path('place-online-orders/', csrf_exempt(OnlinePlaceOrderAPI.as_view()), name='place-online-orders'),
    path('get-order-payment-link/', GetOrderPaymentLinkAPI.as_view(), name='get-order-payment-link'), 
    path('report/forecast/', SalesForecastAPIView.as_view(),name='sales_forecast'),
    
]