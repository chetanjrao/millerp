from rest_framework.views import APIView
from rest_framework.permissions import AllowAny


class ProcessLogin(APIView):

    permission_classes = [ AllowAny ]

    def post(self, request, *args, **kwargs):
        pass
