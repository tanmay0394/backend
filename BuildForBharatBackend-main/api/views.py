from django.shortcuts import render
from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from . import models
from .util import generate_unique_id
from .mailservice import SendMail
from . import serializers
from .renderers import UserRenderer

mail = SendMail()


# Create your views here.
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class UserRegisterView(generics.CreateAPIView):
    serializer_class = serializers.UserRegisterSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = serializers.UserRegisterSerializer(data=request.data)
        if not serializer.is_valid():
            messages: dict = {}
            for key, value in dict(serializer.errors).items():
                messages[key] = value[0]
            return Response(data={'messages': messages, 'status': {'msg': 'failed', 'code': 220}})
        user = serializer.save()
        token = get_tokens_for_user(user)
        return Response({'token': token, 'message': 'Registration Successful.',
                         'status': {'code': 200, 'msg': 'success'}}, status=status.HTTP_200_OK)


class UserLoginView(generics.CreateAPIView):
    serializer_class = serializers.UserLoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = serializers.UserLoginSerializer(data=request.data)
        if not serializer.is_valid():
            messages: dict = {}
            for key, value in dict(serializer.errors).items():
                messages[key] = value[0]
            return Response(data={'messages': messages, 'status': {'msg': 'failed', 'code': 220}})
        username = serializer.data.get('username')
        password = serializer.data.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            token = get_tokens_for_user(user)
            return Response(
                {'token': token, 'message': 'Login Successful.', 'status': {'msg': 'success', 'code': 200}},
                status=status.HTTP_200_OK)
        else:
            return Response({'message': 'Username or Password is not Valid',
                             'status': {'msg': 'success', 'code': 230}}, status=status.HTTP_404_NOT_FOUND)


class VerifyOTP(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        of = request.data.get('of')
        otp = request.data.get('otp')

        user = get_object_or_404(models.User, id=request.user.id)
        if otp is None or otp == "":
            return Response(data={'message': 'Enter otp.', 'status': {'code': 220, 'msg': 'failed'}})
        if of is None or of == "":
            return Response(
                data={'message': 'Submit which otp should verify.', 'status': {'code': 220, 'msg': 'failed'}})
        if of == "gst":
            if user.user_gst.otp != otp:
                return Response(data={'message': 'Enter correct otp.', 'status': {'code': 220, 'msg': 'failed'}})
            user.user_gst.is_otp_used = True
            user.user_gst.gst_verified = True
            user.user_gst.save()
        else:
            if user.user_otp_verification.otp != otp:
                return Response(data={'message': 'Enter correct otp.', 'status': {'code': 220, 'msg': 'failed'}})
            user.user_otp_verification.is_otp_used = True
            user.email_verified = True
            user.save()
            user.user_otp_verification.save()
        return Response(data={'message': 'Successfully OTP verified.', 'status': {'code': 200, 'msg': 'success'}})


class UserDetailsView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        serializer = serializers.UserSerializer(request.user, many=False)
        return Response(data={'user': serializer.data, 'message': 'Successfully retrieved.',
                              'status': {'code': 200, 'msg': 'success'}})


class UploadGSTCertificateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        gst_certificate = request.FILES.get('gst-certificate')
        if gst_certificate is None:
            return Response(
                data={'message': 'Select GST certificate to upload.', 'status': {'code': 230, 'msg': 'failed'}})
        seller_id = f'{generate_unique_id(10)}U{request.user.id}'
        models.SellerGST.objects.get_or_create(user_id=request.user.id, seller_id=seller_id,
                                               certificate=gst_certificate)
        return Response(
            data={'message': 'Successfully certificate uploaded.', 'status': {'code': 200, 'msg': 'success'}})


class UpdateGSTDetailsView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        trade_name = request.data.get('trade-name')
        gst_no = request.data.get('gst-no')
        gst_type = request.data.get('gst-type')
        legal_name = request.data.get('legal-name')
        business_address = request.data.get('business_address')

        if trade_name is None or trade_name == "" or gst_no is None or gst_no == "" or gst_type is None or gst_type == "" or legal_name is None or legal_name == "" or business_address is None or business_address != "":
            return Response(data={'message': 'Enter all details.', 'status': {'code': 230, 'msg': 'failed'}})

        seller_gst = get_object_or_404(models.SellerGST, user=request.user)
        seller_gst.trade_name = trade_name
        seller_gst.gst_no = gst_no
        seller_gst.gst_type = gst_type
        seller_gst.legal_name = legal_name
        seller_gst.business_address = business_address
        seller_gst.save()

        otp = mail.generate_otp()
        seller_gst.gst_otp = otp

        mail.send_otp(request.user, otp, "gst")

        serializer = serializers.SellerGSTDetailsSerializer(seller_gst, many=False)
        return Response(data={'seller_gst': serializer.data, 'message': 'Successfully retrieved.',
                              'status': {'code': 200, 'msg': 'success'}})


class SellerDetailsView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated, ]

    def get(self, request, *args, **kwargs):
        serializer = serializers.SellerGSTDetailsSerializer(request.user.user_gst, many=False)
        return Response(data={'seller_gst': serializer.data, 'message': 'Successfully retrieved.',
                              'status': {'code': 200, 'msg': 'success'}})


class GetBusinessView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated, ]

    def get(self, request, *args, **kwargs):
        user_business = get_object_or_404(models.Business, user=request.user)
        serializer = serializers.BusinessSerializer(user_business, many=False)
        return Response(data={'business': serializer.data, 'message': 'Successfully retrieved.',
                              'status': {'code': 200, 'msg': 'success'}})


class UpdateBusinessView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated, ]

    def post(self, request, *args, **kwargs):
        upload_file = request.data.get('upload-file')
        if upload_file is None or upload_file == "":
            return Response(data={'message': 'Submit action in 0 or 1.', 'status': {'code': 230, 'msg': 'failed'}})

        if int(upload_file) == 1:
            pic = request.FILES.get('profile-pic')
            business = models.Business.update_or_create(user_id=request.user.id,
                                                        defaults={'profile_pic': pic})
            return Response(data={'message': 'Successfully retrieved.', 'status': {'code': 200, 'msg': 'success'}})
        else:
            name = request.data.get('business-name')
            address = request.data.get('business-address')
            email = request.data.get('business-email')
            contact_number = request.data.get('business-contact_number')
            shipping_method = request.data.get('business-shipping_method')

            business = models.Business.update_or_create(user_id=request.user.id,
                                                        defaults={'name': name,
                                                                  'address': address,
                                                                  'email_address': email,
                                                                  'phone_number': contact_number,
                                                                  'shipping_method': shipping_method})
            serializer = serializers.BusinessSerializer(business, many=False)
            return Response(data={'business': serializer.data, 'message': 'Successfully retrieved.',
                                  'status': {'code': 200, 'msg': 'success'}})


class BankDetailsView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated, ]

    def post(self, request, *args, **kwargs):
        if not models.Business.objects.filter(user_id=request.user.id).exists():
            return Response(
                data={'message': 'First create your business profile.', 'status': {'code': 230, 'msg': 'failed'}})

        acc_holder_name = request.data.get('acc-holder-name')
        acc_number = request.data.get('acc-number')
        ifsc = request.data.get('ifsc')

        user_business = get_object_or_404(models.Business, user=request.user)

        bank_details = models.BanksDetails.objects.create(business_id=user_business.id, acc_holder_name=acc_holder_name,
                                                          acc_number=acc_number, ifsc=ifsc)
        serializer = serializers.BankDetailsSerializer(bank_details, many=False)
        return Response(data={'bank': serializer.data, 'message': 'Successfully created.',
                              'status': {'code': 200, 'msg': 'success'}})


class HomeView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated, ]

    def get(self, request, *args, **kwargs):
        return Response(data={'message': 'You are authenticated', 'username': request.user.username},
                        status=status.HTTP_200_OK)
