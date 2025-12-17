from django.urls import path,include
from user_app.View.SignInAPI import SignInView,LogoutView
from user_app.View.ChangePasswordAPI import ChangePasswordView
from user_app.View.UserView import UserView,UserExportView,AdminView
from user_app.View.ForgotPasswordAPI import ForgotPasswordFormView,ForgotPasswordSendLinkView
from user_app.View.AddressView import crmAddressAPI
from .views import ContactUsView

#mobile api
from user_app.MobileAPIView.LoginViewAPI import LoginView
from user_app.MobileAPIView.SignUpView import SignUpView
from user_app.MobileAPIView.VerifyOTPViewAPI import VerifyOtpAPIView
from user_app.MobileAPIView.AddressViewAPI import AddressListView, AddressCreateView
from user_app.MobileAPIView.UserManagementView import UserUpdateView, UserDeleteView, GetUserView
from user_app.MobileAPIView.CustomerView import CustomerListView

#web api
from user_app.WebView.SignInView import WebSignInView
from user_app.WebView.SignUpView import WebSignUpView
from user_app.WebView.ProfileView import WebProfileView
from user_app.WebView.DeactivateAccountView import DeactivateAccountAPI
from user_app.WebView.AddressView import AddressAPI, CountriesAPI, StatesAPI,CitiesAPI
from user_app.WebView.VerifyOTPViewAPI import WebVerifyOtpAPIView

urlpatterns = [
    
    path('signin/',SignInView.as_view(),name='sign-in'),
    path('change-password/',ChangePasswordView.as_view(),name='change-password'),
    path('logout/',LogoutView.as_view(),name='logout'),
    path('forgot-password/',ForgotPasswordSendLinkView.as_view(),name='forgot-password-send-link'),
    path('forgot-password/<str:reset_token>/',ForgotPasswordFormView.as_view(),name='forgot-password'),
    path('',UserView.as_view(),name='users'),
    path('admin/',AdminView.as_view(),name='admin'),
    path('admin/<int:id>/',AdminView.as_view(),name='admin'),
    path('<int:id>/',UserView.as_view(),name='users'),
    path('excel/',UserExportView.as_view(),name='users-excel'),
    path('address/',crmAddressAPI.as_view(),name='address'),
    path('address/<int:id>/',crmAddressAPI.as_view(),name='address'),
    path('contact-us/',ContactUsView.as_view(),name='contact-us'),
    
    #mobile api
    path('mobile/login/', LoginView.as_view() , name='login' ),
    path('mobile/signup/',SignUpView.as_view(),name='signup'),
    path("mobile/verify-otp/", VerifyOtpAPIView.as_view(), name="verify-otp"),
    path("mobile/address/list/", AddressListView.as_view(), name="address-list"),
    path("mobile/address/add/", AddressCreateView.as_view(), name="add-address"),
    path('mobile/update-profile/',UserUpdateView.as_view(),name='user-update'),
    path('mobile/delete-account/',UserDeleteView.as_view(), name='delete-account'),
    path('mobile/get-user-profile/', GetUserView.as_view(), name="user-detail"),
    path('mobile/customer-list/', CustomerListView.as_view(), name="customer-list"),
    
    #web api
    path('web/signup/',WebSignUpView.as_view(),name='signup'),
    path('web/signin/',WebSignInView.as_view(),name='signin'),
    path('web/verify-otp/',WebVerifyOtpAPIView.as_view(), name= 'web-verify-otp'),
    path('web/profile/',WebProfileView.as_view(),name='user-profile'),
    path('web/deactivate/', DeactivateAccountAPI.as_view(), name='deactivate'),
    path('web/address/',AddressAPI.as_view(),name='address'),
    path('web/address/<int:id>/',AddressAPI.as_view(),name='address'),
    path('web/countries/',CountriesAPI.as_view(),name='countries'),
    path('web/countries/<int:id>/',CountriesAPI.as_view(),name='countries'),
    path('web/states/',StatesAPI.as_view(),name='states'),
    path('web/states/<int:id>/',StatesAPI.as_view(),name='states'),
    path('web/cities/',CitiesAPI.as_view(),name='cities'),
    path('web/cities/<int:id>/',CitiesAPI.as_view(),name='cities'),   
]