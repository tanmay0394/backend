from django.db import models
from django.apps import apps
from django.contrib import auth
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.utils.translation import gettext_lazy as _

from .filepath import gst_certificate_path, business_profile_pic_path
from .util import validate_name, validate_contact_number

from .validators import UnicodeContactNumberValidator, UnicodeNameValidator


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """
        Create and save a user with the given username, email, and password.
        """
        if not email:
            raise ValueError("The given username must be set")
        email = self.normalize_email(email)
        # Lookup the real model class from the global app registry so this
        # manager method can be used in migrations. This is fine because
        # managers are by definition working on the real model.
        GlobalUserModel = apps.get_model(
            self.model._meta.app_label, self.model._meta.object_name
        )
        user = self.model(email=email, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)

    def with_perm(
            self, perm, is_active=True, include_superusers=True, backend=None, obj=None
    ):
        if backend is None:
            backends = auth._get_backends(return_tuples=True)
            if len(backends) == 1:
                backend, _ = backends[0]
            else:
                raise ValueError(
                    "You have multiple authentication backends configured and "
                    "therefore must provide the `backend` argument."
                )
        elif not isinstance(backend, str):
            raise TypeError(
                "backend must be a dotted import path string (got %r)." % backend
            )
        else:
            backend = auth.load_backend(backend)
        if hasattr(backend, "with_perm"):
            return backend.with_perm(
                perm,
                is_active=is_active,
                include_superusers=include_superusers,
                obj=obj,
            )
        return self.none()


class User(AbstractUser):
    username = None
    first_name = None
    last_name = None
    name = models.CharField(max_length=500, null=False, validators=[validate_name, ])
    email = models.EmailField(_('email address'), unique=True,
                              error_messages={
                                  "unique": _("This email is already in use."),
                              })
    contact_number = models.CharField(_('contact number'), max_length=15, unique=True,
                                      validators=[validate_contact_number, ],
                                      error_messages={
                                          "unique": _("This contact number is already in use."),
                                      })
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_("Designates whether the user can log into this admin site."),
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )
    groups = models.ManyToManyField(Group, related_name='custom_users')
    permissions = models.ManyToManyField(Permission, related_name='user_permissions')

    objects = UserManager()

    # EMAIL_FIELD = "email"
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name_plural = "Users"


class UserDetails(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_details')
    email_verified = models.BooleanField(default=False)
    phone_number_verified = models.BooleanField(default=False)
    is_seller = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Details"


class OTPVerification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_otp_verification')
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    email_id = models.CharField(max_length=250, null=True, blank=True)
    otp = models.CharField(max_length=10)
    is_otp_used = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "OTP Verification"


class SellerGST(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_gst')
    seller_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    certificate = models.ImageField(upload_to=gst_certificate_path, null=True, blank=True)
    trade_name = models.CharField(max_length=200, null=True)
    gst_number = models.CharField(max_length=100, null=True)
    gst_type = models.CharField(max_length=100, null=True)
    legal_name = models.CharField(max_length=200, null=True)
    otp = models.CharField(max_length=10, null=True, blank=True)
    is_otp_used = models.BooleanField(default=False)
    gst_verified = models.BooleanField(default=False)
    business_address = models.TextField(null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.seller_id}_{self.user.name}'

    class Meta:
        verbose_name_plural = "Seller GST Details"


class Business(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_business')
    profile_pic = models.ImageField(upload_to=business_profile_pic_path, help_text='Upload file for business profile.')
    name = models.CharField(max_length=250, null=True)
    store_name = models.CharField(max_length=200, null=True)
    address = models.JSONField(null=True, blank=True)
    email_address = models.CharField(max_length=250, null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    shipping_method = models.CharField(max_length=250, null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.name}'

    class Meta:
        verbose_name_plural = "User Business Profiles"


class BanksDetails(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='business_bank_details')
    acc_holder_name = models.CharField(max_length=250, null=False)
    acc_number = models.CharField(max_length=100, null=False)
    ifsc = models.CharField(max_length=100, null=False)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.business}'

    class Meta:
        verbose_name_plural = "Business Bank Details"
