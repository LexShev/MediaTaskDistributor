

def ask_permissions(worker_id):
    admin_group = [0, 1]
    editors_group = [2, 3, 4, 5]

    if worker_id in admin_group:
        return {'list': True, 'month': False, 'week': True}
    elif worker_id in editors_group:
        return {'list': True, 'month': False, 'week': True}
    else:
        return {'list': False, 'month': False, 'week': False}