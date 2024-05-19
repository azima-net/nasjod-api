from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    confirm_password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            'id', 'identifier', 'username', 'email', 'sex', 'birth_date', 'first_name', 
            'last_name', 'phone_number','created_at', 'updated_at', 'address',
            'photo', 'password', 'confirm_password',
        ]
        extra_kwargs = {
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
        }
    
    def validate(self, data):
        password = data.get('password')
        confirm_password = data.pop('confirm_password', None)

        if password and confirm_password:
            if password != confirm_password:
                raise serializers.ValidationError({"password": "Passwords must match."})
        return data

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        if password:
            instance.set_password(password)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """Modify the representation of the user instance."""
        representation = super().to_representation(instance)
        # representation.pop('password', None)  # Remove the password from the representation
        return representation
