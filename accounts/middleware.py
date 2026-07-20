from django.shortcuts import redirect
from django.urls import reverse

class OnboardingMiddleware:
    """
    Middleware to ensure users have completed their onboarding selection
    before accessing dashboard pages.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.user.has_completed_onboarding:
            # We want to protect certain URLs, like dashboard. 
            # Or conversely, allow only specific URLs.
            # Assuming dashboard paths start with /accounts/ or specific dashboard paths.
            # We shouldn't block /admin/ or API endpoints or static files.
            path = request.path_info
            
            # Allow logout, selection page, API, and admin
            allowed_paths = [
                reverse('accounts:logout'), 
                reverse('core:selection'),
                reverse('core:api_selection_submit'),
            ]
            
            # We can either protect specific paths or protect everything except allowed paths.
            # Since users might want to browse the site, the requirement was: 
            # "بتونه ریدایرکت بشه به داشبورد کاربریش... یعنی تا این صفحه روانتخاب نکنه نتونه وارد صفحات داشبورد بشه"
            # So they are only blocked from DASHBOARD, not the main site? 
            # If dashboard is /accounts/dashboard/, we can check for that.
            # Wait, usually the dashboard is the entire profile area.
            if path.startswith('/accounts/') and path not in allowed_paths and not path.startswith('/accounts/api/'):
                if not path.startswith('/accounts/login/'): # Just in case
                    return redirect('core:selection')
                    
        response = self.get_response(request)
        return response
