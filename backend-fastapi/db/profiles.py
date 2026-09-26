import django_setup  # noqa: F401  (must run before importing Django models)

from asgiref.sync import sync_to_async
from users.models import Profile


@sync_to_async
def get_or_create_profile(uid: str, email: str, display_name: str = "", role: str = None):
    profile, created = Profile.objects.get_or_create(
        firebase_uid=uid,
        defaults={
            "email": email or "",
            "display_name": display_name,
            "role": role or Profile.Role.STUDENT,
        },
    )
    return profile, created


@sync_to_async
def get_profile(uid: str):
    try:
        return Profile.objects.get(firebase_uid=uid)
    except Profile.DoesNotExist:
        return None