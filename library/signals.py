from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver

from .models import User, UserRole


ROLE_PERMISSION_MAP = {
    UserRole.ADMIN: {
        'library.change_user',
        'library.delete_user',
        'library.view_user',
    },
    UserRole.WORKER: {
        'library.add_author',
        'library.change_author',
        'library.view_author',
        'library.add_book',
        'library.change_book',
        'library.view_book',
        'library.add_bookcopy',
        'library.change_bookcopy',
        'library.view_bookcopy',
        'library.add_category',
        'library.change_category',
        'library.view_category',
    },
    UserRole.USER: {
        'library.borrow_book',
        'library.return_book',
        'library.pay_fine',
        'library.reserve_book',
        'library.cancel_reservation',
        'library.view_book',
        'library.view_bookcopy',
    },
}


def _permission_from_label(label: str):
    app_label, codename = label.split('.', 1)
    return Permission.objects.select_related('content_type').get(
        content_type__app_label=app_label,
        codename=codename,
    )


def sync_role_group_permissions():
    for role, permission_labels in ROLE_PERMISSION_MAP.items():
        group, _ = Group.objects.get_or_create(name=role)
        permissions = [_permission_from_label(label) for label in permission_labels]
        group.permissions.set(permissions)


def sync_user_role_membership(user: User):
    if user.role not in UserRole.values:
        user.role = UserRole.USER

    if user.role in {UserRole.ADMIN, UserRole.WORKER} and not user.is_superuser:
        user.is_staff = True
    elif not user.is_superuser:
        user.is_staff = False

    User.objects.filter(pk=user.pk).update(role=user.role, is_staff=user.is_staff)

    for group_name in UserRole.values:
        group = Group.objects.filter(name=group_name).first()
        if group is None:
            continue
        if group_name == user.role:
            user.groups.add(group)
        else:
            user.groups.remove(group)


@receiver(post_migrate)
def ensure_role_groups(sender, **kwargs):
    if sender.name != 'library':
        return

    sync_role_group_permissions()
    for user in User.objects.all().iterator():
        sync_user_role_membership(user)


@receiver(post_save, sender=User)
def apply_role_membership(sender, instance, created, **kwargs):
    if created:
        sync_user_role_membership(instance)
        return

    desired_staff = instance.role in {UserRole.ADMIN, UserRole.WORKER}
    if instance.is_superuser:
        desired_staff = True

    if instance.role not in UserRole.values:
        instance.role = UserRole.USER

    current_groups = set(instance.groups.values_list('name', flat=True))
    desired_groups = {instance.role}

    if current_groups != desired_groups or instance.is_staff != desired_staff:
        instance.is_staff = desired_staff
        User.objects.filter(pk=instance.pk).update(role=instance.role, is_staff=instance.is_staff)

        for group_name in UserRole.values:
            group = Group.objects.filter(name=group_name).first()
            if group is None:
                continue
            if group_name == instance.role:
                instance.groups.add(group)
            else:
                instance.groups.remove(group)