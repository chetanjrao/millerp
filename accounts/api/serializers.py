from core.models import Owner
from re import U
from rest_framework import serializers
from ..models import User, OTP
from django.utils.timezone import now, datetime
from random import randint

# class UserSerializer(serializers.ModelSerializer):

#     class Meta:
#         model = User

#     def create(self, validated_data):


class OTPSerializer(serializers.Serializer):
    user = serializers.CharField(max_length=10)
    role = serializers.IntegerField()

    def validate_user(self, user):
        try:
            __pre_check = User.objects.get(mobile='+91{}'.format(user), role=3)
            Owner.objects.get(user=__pre_check)
        except (User.DoesNotExist, Owner.DoesNotExist):
            raise serializers.ValidationError("Mobile is not associated with any user")
        return '+91{}'.format(user)

    def create(self, validated_data):
        otp = randint(1000, 9999)
        expiry = now() + datetime.timedelta(minutes=15)
        otp_document = OTP.objects.create(mobile=validated_data["user"], otp=otp, expires_at=expiry)
        # TODO: Send OTP to mobile function
        print(otp)
        return otp_document

