def show_qab_processor(request):
    excluded_paths = ['/login/', '/register/', '/complete-profile/', '/health/']
    return {
        'show_qab': request.path not in excluded_paths
    }
