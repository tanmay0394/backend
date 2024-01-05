from rest_framework_simplejwt import views as jwt_views
from django.urls import path
from . import views

urlpatterns = [
    # """ Authentication """,
    path('register', views.UserRegisterView.as_view()),
    path('login', views.UserLoginView.as_view()),
    path('token/refresh', jwt_views.TokenRefreshView.as_view()),
    path('verify/otp', views.VerifyOTP.as_view()),
    path('logout', jwt_views.TokenBlacklistView.as_view()),

    # """ Seller Registration """,
    path('upload/gst-certificate', views.UploadGSTCertificateView.as_view()),
    path('update/gst-details', views.UpdateGSTDetailsView.as_view()),
    path('update/business-profile', views.UpdateBusinessView.as_view()),

    # """ Payment Details """
    path('create/bank-details', views.BankDetailsView.as_view()),

    # """ Retrieve Data """
    path('user-details', views.UserDetailsView.as_view()),
    path('business-details', views.GetBusinessView.as_view()),
    path('seller-details', views.SellerDetailsView.as_view()),
]
