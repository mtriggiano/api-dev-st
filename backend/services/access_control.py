from models import UserInstanceAccess


def normalize_instance_names(instance_names):
    if not isinstance(instance_names, list):
        return []

    normalized = {
        str(name).strip()
        for name in instance_names
        if isinstance(name, str) and str(name).strip()
    }
    return sorted(normalized)


def get_user_allowed_instances(user):
    if not user:
        return set()

    if user.role == 'admin':
        return None

    return {access.instance_name for access in user.instance_accesses}


def can_user_access_instance(user, instance_name):
    if not user or not instance_name:
        return False

    if user.role == 'admin':
        return True

    return instance_name in {access.instance_name for access in user.instance_accesses}


def filter_instances_for_user(user, instances):
    if not user:
        return []

    if user.role == 'admin':
        return instances

    allowed = {access.instance_name for access in user.instance_accesses}
    return [instance for instance in instances if instance.get('name') in allowed]


def sync_user_instance_access(user, instance_names):
    normalized = normalize_instance_names(instance_names)
    current_by_name = {access.instance_name: access for access in user.instance_accesses}

    for access in list(user.instance_accesses):
        if access.instance_name not in normalized:
            user.instance_accesses.remove(access)

    for instance_name in normalized:
        if instance_name not in current_by_name:
            user.instance_accesses.append(UserInstanceAccess(instance_name=instance_name))


def grant_user_instance_access(user, instance_name):
    if not user or not instance_name or user.role == 'admin':
        return

    if any(access.instance_name == instance_name for access in user.instance_accesses):
        return

    user.instance_accesses.append(UserInstanceAccess(instance_name=instance_name))
