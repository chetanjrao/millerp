from rest_framework.permissions import BasePermission

class OwnerPermission(BasePermission):

    def has_permission(self, request, view):
        request.user.role == 3

        