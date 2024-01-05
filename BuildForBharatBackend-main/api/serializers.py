from . import models
from rest_framework import serializers
from .mailservice import SendMail

mail = SendMail()


class UserRegisterSerializer(serializers.ModelSerializer):
    """user register serializer"""
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """validate attributes is valid or not"""
        print('attrs: ', attrs)
        return attrs

    def create(self, validated_data):
        user = models.User.objects.create_user(
            name=validated_data['name'],
            email=validated_data['email'].lower(),
            contact_number=validated_data['contact_number'],
            password=validated_data['password'],
        )
        models.UserDetails.objects.create(user_id=user.id)
        otp = mail.generate_otp()
        models.OTPVerification.objects.create(user_id=user.id, email_id=user.email, phone_number=user.contact_number,
                                              otp=otp)
        mail.send_otp(user, otp, "email")
        return user

    class Meta:
        model = models.User
        fields = ["id", "name", "email", "contact_number", "password"]


class UserLoginSerializer(serializers.ModelSerializer):
    """user login serializer"""
    email = serializers.EmailField(max_length=255)

    class Meta:
        model = models.User
        fields = ["email", "password"]


class UserSerializer(serializers.ModelSerializer):
    email_verified = serializers.SerializerMethodField(method_name='get_email_verified')
    number_verified = serializers.SerializerMethodField(method_name='get_phone_verified')
    is_seller = serializers.SerializerMethodField(method_name='get_is_seller')

    @staticmethod
    def get_email_verified(instance):
        return instance.user_details.email_verified

    @staticmethod
    def get_phone_verified(instance):
        return instance.user_details.phone_number_verified

    @staticmethod
    def get_is_seller(instance):
        return instance.user_details.is_seller

    class Meta:
        model = models.User
        fields = ['name', 'email', 'contact_number', 'is_active', 'email_verified', 'number_verified', 'is_seller']


class SellerGSTDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SellerGST
        fields = ['id', 'seller_id', 'certificate', 'trade_name', 'gst_number', 'gst_type', 'legal_name',
                  'business_address', 'gst_verified']


class BusinessSerializer(serializers.ModelSerializer):

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['bank_details'] = BankDetailsSerializer(instance.business_bank_details.all(), many=True).data
        return response

    class Meta:
        model = models.Business
        fields = ['name', 'store_name', 'address', 'email_address', 'phone_number', 'shipping_method', ]


class BankDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.BanksDetails
        fields = ['acc_holder_name', 'acc_number', 'ifsc']
