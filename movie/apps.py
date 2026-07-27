from django.apps import AppConfig

class MovieConfig(AppConfig):
    name = 'movie'
    verbose_name = 'فیلم و سریال'

    def ready(self):
        # Monkey patch AdminSite to sort models in the custom order requested by the user
        from django.contrib import admin

        original_get_app_list = admin.AdminSite.get_app_list

        def get_app_list(self, request, app_label=None):
            app_list = original_get_app_list(self, request, app_label)
            
            custom_order = {
                'movie': 1,
                'moviecollectionitem': 2,
                'series': 3,
                'season': 4,
                'episode': 5,
                'seriestrailer': 6,
                'person': 7,
                'country': 8,
                'genre': 9,
                'quality': 10,
                'moviecomment': 11,
                'seriescomment': 12,
            }

            from django.contrib.contenttypes.models import ContentType
            from django.utils.safestring import mark_safe

            for app in app_list:
                if app['app_label'] == 'movie':
                    app['models'].sort(key=lambda x: custom_order.get(x['object_name'].lower(), 99))
                    # Import dynamically to avoid circular import errors
                    from core.models import AdminNotification
                    for model in app['models']:
                        obj_name = model['object_name'].lower()
                        try:
                            ct = ContentType.objects.get(app_label='movie', model=obj_name)
                            unread_count = AdminNotification.objects.filter(content_type=ct, is_read=False).count()
                            if unread_count > 0:
                                model['name'] = mark_safe(
                                    f"{model['name']} <span class='badge' style='background-color: #e41a1a; color: white; border-radius: 50%; padding: 2px 6px; font-size: 11px; margin-right: 8px; font-weight: bold; vertical-align: middle;'>{unread_count}</span>"
                                )
                        except Exception:
                            pass
            return app_list

        admin.AdminSite.get_app_list = get_app_list
