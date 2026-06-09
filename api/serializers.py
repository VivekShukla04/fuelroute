from rest_framework import serializers


class RouteRequestSerializer(serializers.Serializer):
    start = serializers.CharField(required=True, help_text="Start location (city, state or address within USA)")
    finish = serializers.CharField(required=True, help_text="Finish location (city, state or address within USA)")


class FuelStopSerializer(serializers.Serializer):
    name = serializers.CharField()
    address = serializers.CharField()
    city = serializers.CharField()
    state = serializers.CharField()
    price_per_gallon = serializers.FloatField()
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    distance_from_start_mi = serializers.FloatField()
    estimated_gallons = serializers.FloatField()
    cost = serializers.FloatField()


class RouteResponseSerializer(serializers.Serializer):
    start_location = serializers.CharField()
    finish_location = serializers.CharField()
    start_coordinates = serializers.ListField(child=serializers.FloatField())
    finish_coordinates = serializers.ListField(child=serializers.FloatField())
    total_distance_miles = serializers.FloatField()
    total_fuel_cost = serializers.FloatField()
    total_gallons = serializers.FloatField()
    fuel_stops = FuelStopSerializer(many=True)
    route_geometry = serializers.CharField()
    route_instructions = serializers.ListField(child=serializers.DictField(), required=False)
