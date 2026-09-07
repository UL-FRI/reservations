"""Serializers for REST."""

from django.contrib.auth.models import User
from reservations.models import (NResources, Reservable, ReservableSet,
                                 ReservableType, Reservation, Resource)
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
	class Meta:
		model = User
		fields = ("id", "first_name", "last_name", "url")

class ResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resource
        fields = "__all__"


class ReservableNResourcesSerializer(serializers.ModelSerializer):
    resource = ResourceSerializer()

    class Meta:
        model = NResources
        fields = ("id", "resource", "n", "url")


class ReservableSerializer(serializers.ModelSerializer):
    nresources_set = ReservableNResourcesSerializer(many=True, read_only=True)
    type = serializers.SlugRelatedField(slug_field="slug", queryset=ReservableType.objects.all())

    class Meta:
        model = Reservable
        fields = ("id", "slug", "type", "name", "nresources_set", "url")


class ReservableSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReservableSet
        fields = ("name", "slug", "reservables", "url")


class ReservationSerializer(serializers.ModelSerializer):
    """Serializer for the Reservation model."""
    owners = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Reservation
        fields = [
            "reason",
            "start",
            "end",
            "owners",
            "reservables",
            "requirements",
            "created_at",
            "updated_at",
            "id",
            "url",
        ]
