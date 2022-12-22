"""Serializers for REST."""

from rest_framework import serializers

from reservations.models import (
    NResources,
    Reservable,
    ReservableSet,
    Reservation,
    Resource,
)


class ResourceSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Resource
        fields = "__all__"


class ReservableNResourcesSerializer(serializers.ModelSerializer):
    resource = ResourceSerializer()

    class Meta:
        model = NResources
        fields = ("id", "resource", "n", "url")


class ReservableSerializer(serializers.HyperlinkedModelSerializer):
    nresources_set = ReservableNResourcesSerializer(many=True, read_only=True)

    class Meta:
        model = Reservable
        fields = ("id", "slug", "type", "name", "nresources_set", "url")


class ReservableSetSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ReservableSet
        fields = ("name", "slug", "reservables", "url")


class ReservationSerializer(serializers.HyperlinkedModelSerializer):
    reservables = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    owners = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Reservation
        fields = [
            "reason",
            "start",
            "end",
            "owners",
            "reservables",
            "requirements",
            "id",
            "url",
        ]
