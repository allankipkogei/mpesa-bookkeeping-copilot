from rest_framework import generics, permissions
from .serializers import UserSerializer

class UserCreateView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = UserSerializer
