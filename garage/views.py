from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from django.db.models import Avg, Q
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from geopy.distance import geodesic

from .models import Garage, ParkingSpot
from .serializers import (
    GarageSerializer, GarageDetailSerializer,
    ParkingSpotSerializer, GarageRegistrationSerializer,
    GarageUpdateSerializer
)

####################### Garage Detail View #######################

class GarageDetailView(APIView):
    def get(self, request, id):
        try:
            garage = Garage.objects.annotate(
                average_rating=Avg('reviews__rating')
            ).get(id=id)

            data = GarageDetailSerializer(garage, context={'request': request}).data
            data["number_of_spots"] = garage.spots.count()

            return Response(data)
        except Garage.DoesNotExist:
            return Response({"error": "Garage not found"}, status=status.HTTP_404_NOT_FOUND)

####################### Get Spots in Garage #######################

class GarageSpotsView(APIView):
    def get(self, request, id):
        spots = ParkingSpot.objects.filter(garage_id=id)
        serializer = ParkingSpotSerializer(spots, many=True)
        return Response(serializer.data)

####################### Nearby Garages View #######################

class NearbyGaragesView(generics.ListAPIView):
    serializer_class = GarageSerializer

    def get_queryset(self):
        queryset = Garage.objects.all()
        lat = self.request.query_params.get('lat')
        lon = self.request.query_params.get('lon')
        query = self.request.query_params.get('search')

        if query:
            queryset = queryset.filter(Q(name__icontains=query) | Q(address__icontains=query))

        if lat and lon:
            user_location = (float(lat), float(lon))
            queryset = sorted(queryset, key=lambda garage: geodesic(user_location, (garage.latitude, garage.longitude)).km)

        return queryset

    def get_serializer_context(self):
        return {'request': self.request}

####################### Register Garage #######################

class GarageRegisterView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != 'garage_owner':
            return Response({"detail": "Only garage owners can register garages."}, status=403)

        serializer = GarageRegistrationSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            garage = serializer.save()
            return Response({"detail": "Garage registered successfully.", "garage_id": garage.id}, status=201)
        return Response(serializer.errors, status=400)

####################### Update Garage #######################

class GarageUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, id):
        garage = get_object_or_404(Garage, id=id, owner=request.user)

        serializer = GarageUpdateSerializer(garage, data=request.data, partial=True)

        if serializer.is_valid():
            updated_instance = serializer.save()
            return Response({
                "detail": "Garage updated successfully.",
                "garage_id": updated_instance.id,
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

####################### Garage Occupancy View #######################

class GarageOccupancyView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, garage_id):
        try:
            garage = Garage.objects.get(id=garage_id)
        except Garage.DoesNotExist:
            return Response({'error': 'Garage not found'}, status=404)

        all_spots = ParkingSpot.objects.filter(garage=garage)
        total_spots = all_spots.count()
        occupied_spots = all_spots.filter(status__in=['reserved', 'occupied']).count()
        available_spots = total_spots - occupied_spots

        return Response({
            'garage_id': garage.id,
            'total_spots': total_spots,
            'occupied_spots': occupied_spots,
            'available_spots': available_spots
        })
