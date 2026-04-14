from rest_framework.permissions import DjangoObjectPermissions


class DjangoObjectPermissionsOrReadOnly(DjangoObjectPermissions):
    authenticated_users_only = False
    