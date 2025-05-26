# core/context_processors.py
def navigation(request):
    nav_items = {
        'super_super': [
            {'name': 'System Dashboard', 'url': 'system_dashboard', 'icon': 'bi-speedometer2'},
            {'name': 'User Management', 'url': 'user_management', 'icon': 'bi-people'},
            {'name': 'Content Review', 'url': 'content_review', 'icon': 'bi-file-earmark-check'},
            {'name': 'System Settings', 'url': 'system_settings', 'icon': 'bi-gear'},
        ],
        'super': [
            {'name': 'Admin Dashboard', 'url': 'admin_dashboard', 'icon': 'bi-speedometer2'},
            {'name': 'User Management', 'url': 'user_management', 'icon': 'bi-people'},
            {'name': 'Content Review', 'url': 'content_review', 'icon': 'bi-file-earmark-check'},
        ],
        'admin': [
            {'name': 'Dashboard', 'url': 'admin_dashboard', 'icon': 'bi-speedometer2'},
            {'name': 'Content Review', 'url': 'content_review', 'icon': 'bi-file-earmark-check'},
        ],
        'default': [
            {'name': 'Home', 'url': 'home', 'icon': 'bi-house'},
            {'name': 'Challenges', 'url': 'challenges', 'icon': 'bi-trophy'},
            {'name': 'Opportunities', 'url': 'opportunities', 'icon': 'bi-briefcase'},
        ]
    }
    
    if request.user.is_authenticated:
        user_role = request.user.role
        return {
            'main_nav': nav_items.get(user_role, nav_items['default']),
            'admin_nav': nav_items.get(user_role, []) if user_role in ['super_super', 'super', 'admin'] else []
        }
    return {'main_nav': [], 'admin_nav': []}