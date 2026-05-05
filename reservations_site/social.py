from django.contrib.auth.models import Group
from rest_framework.utils import json


def roles_to_groups(backend, details, response, user=None, *args, **kwargs):
    if backend.name != 'oidc':
        return

    if user is None:
        return

    groups = json.loads(response.get('roles', 'null')) or []
    user.groups.clear()
    for group in groups:
        group, _ = Group.objects.get_or_create(name=group)
        user.groups.add(group)
