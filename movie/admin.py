from django.contrib import admin, messages
from django.db.models import Q

from modeltranslation.admin import TranslationAdmin, TranslationTabularInline, TranslationStackedInline
from .models import (
    Person, Country, Genre, Quality, Movie, Series, Season, Episode,
    EpisodeVideo, MovieVideo, MovieCollectionItem, MovieCollectionItemVideo, SeriesTrailer, MovieComment, SeriesComment,
    ContentIngestion
)

from core.models import AdminNotification

# Custom Mixin to mark notifications as read when an admin opens the change view
class NotificationMarkReadMixin:
    def change_view(self, request, object_id, form_url='', extra_context=None):
        from django.contrib.contenttypes.models import ContentType
        try:
            ct = ContentType.objects.get_for_model(self.model)
            AdminNotification.objects.filter(content_type=ct, object_id=object_id).update(is_read=True)
        except Exception:
            pass
        return super().change_view(request, object_id, form_url, extra_context)


# Generic Searchable Autocomplete Filter Base for Sidebar
class AutocompleteSidebarFilter(admin.SimpleListFilter):
    template = 'admin/autocomplete_sidebar_filter.html'
    placeholder = 'جستجو و انتخاب...'

    def lookups(self, request, model_admin):
        return [('dummy', 'dummy')]

    def choices(self, changelist):
        params = changelist.get_filters_params()
        current_val = self.value()
        
        # Clean params to prevent list formatting in template hidden inputs
        cleaned_params = {}
        for k, v in params.items():
            if isinstance(v, (list, tuple)):
                cleaned_params[k] = v[0] if v else ''
            else:
                cleaned_params[k] = v
                
        current_text = ''
        if current_val and current_val != 'dummy':
            try:
                current_text = str(self.search_model_class.objects.get(id=current_val))
            except self.search_model_class.DoesNotExist:
                pass
                
        yield {
            'current_value': current_val if (current_val and current_val != 'dummy') else '',
            'current_text': current_text,
            'all_params': cleaned_params,
        }


# 1. Search filter for Genres
class GenreSearchFilter(AutocompleteSidebarFilter):
    title = 'ژانر (جستجو)'
    parameter_name = 'genres'
    target_model_name = 'movie'
    target_field_name = 'genres'
    search_model_class = Genre
    placeholder = 'نام ژانر را بنویسید...'

    def queryset(self, request, queryset):
        val = self.value()
        if val and val != 'dummy':
            return queryset.filter(genres__id=val)
        return queryset


# 2. Search filter for Countries
class CountrySearchFilter(AutocompleteSidebarFilter):
    title = 'کشور (جستجو)'
    parameter_name = 'country'
    target_model_name = 'movie'
    target_field_name = 'country'
    search_model_class = Country
    placeholder = 'نام کشور را بنویسید...'

    def queryset(self, request, queryset):
        val = self.value()
        if val and val != 'dummy':
            return queryset.filter(country_id=val)
        return queryset


# 3. Search filter for Movies
class MovieSearchFilter(AutocompleteSidebarFilter):
    title = 'فیلم اصلی (جستجو)'
    parameter_name = 'movie'
    target_model_name = 'moviecollectionitem'
    target_field_name = 'movie'
    search_model_class = Movie
    placeholder = 'نام فیلم را بنویسید...'

    def queryset(self, request, queryset):
        val = self.value()
        if val and val != 'dummy':
            return queryset.filter(movie_id=val)
        return queryset


# 4. Search filter for Series
class SeriesSearchFilter(AutocompleteSidebarFilter):
    title = 'سریال اصلی (جستجو)'
    parameter_name = 'series'
    target_model_name = 'season'
    target_field_name = 'series'
    search_model_class = Series
    placeholder = 'نام سریال را بنویسید...'

    def queryset(self, request, queryset):
        val = self.value()
        if val and val != 'dummy':
            if hasattr(queryset.model, 'season'):
                # For Episode model
                return queryset.filter(season__series_id=val)
            else:
                # For Season, SeriesTrailer, Comment models
                return queryset.filter(series_id=val)
        return queryset


# 5. Search filter for Seasons
class SeasonSearchFilter(AutocompleteSidebarFilter):
    title = 'فصل (جستجو)'
    parameter_name = 'season'
    target_model_name = 'episode'
    target_field_name = 'season'
    search_model_class = Season
    placeholder = 'نام فصل یا سریال...'

    def queryset(self, request, queryset):
        val = self.value()
        if val and val != 'dummy':
            return queryset.filter(season_id=val)
        return queryset


@admin.register(Quality)
class QualityAdmin(admin.ModelAdmin):
    list_display = ['title', 'weight']
    search_fields = ['title']


@admin.register(Person)
class PersonAdmin(TranslationAdmin):
    list_display = ['name', 'is_actor', 'is_director', 'slug']
    list_filter = ['is_actor', 'is_director']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'bio']


@admin.register(Country)
class CountryAdmin(TranslationAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


@admin.register(Genre)
class GenreAdmin(TranslationAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


class MovieVideoInline(admin.TabularInline):
    model = MovieVideo
    extra = 1


class MovieCollectionItemInline(TranslationTabularInline):
    model = MovieCollectionItem
    extra = 1
    fields = ('part_number', 'title', 'duration')


@admin.register(Movie)
class MovieAdmin(TranslationAdmin):
    list_display = ['title', 'english_title_primary', 'english_title_secondary', 'imdb_rating', 'created_at']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [MovieVideoInline, MovieCollectionItemInline]
    autocomplete_fields = ['country', 'genres', 'actors', 'director']
    search_fields = ['title', 'english_title_primary', 'english_title_secondary', 'description', 'seo_title', 'meta_description']
    list_filter = [CountrySearchFilter, GenreSearchFilter, 'highest_quality', 'age_limit']
    actions = ['sync_from_tmdb']

    def sync_from_tmdb(self, request, queryset):
        client = TMDBClient()
        success_count = 0
        fail_count = 0
        error_msgs = []
        for item in queryset:
            try:
                client.sync_existing_instance(item)
                success_count += 1
            except Exception as e:
                fail_count += 1
                error_msgs.append(f"فیلم «{item.title}»: {str(e)}")
        
        if success_count:
            messages.success(request, f"اطلاعات {success_count} فیلم با موفقیت از TMDB به‌روزرسانی شد.")
        if fail_count:
            messages.error(request, f"بروزرسانی {fail_count} فیلم با خطا مواجه شد: " + " | ".join(error_msgs))
    sync_from_tmdb.short_description = "بروزرسانی و همگام‌سازی اطلاعات از TMDB"



class SeasonInline(TranslationTabularInline):
    model = Season
    extra = 1


class SeriesTrailerInline(admin.TabularInline):
    model = SeriesTrailer
    extra = 1


@admin.register(Series)
class SeriesAdmin(TranslationAdmin):
    list_display = ['title', 'english_title_primary', 'english_title_secondary', 'imdb_rating', 'created_at']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [SeasonInline, SeriesTrailerInline]
    autocomplete_fields = ['country', 'genres', 'actors', 'director']
    search_fields = ['title', 'english_title_primary', 'english_title_secondary', 'description', 'seo_title', 'meta_description']
    list_filter = [CountrySearchFilter, GenreSearchFilter, 'highest_quality', 'age_limit']
    actions = ['sync_from_tmdb']

    def sync_from_tmdb(self, request, queryset):
        client = TMDBClient()
        success_count = 0
        fail_count = 0
        for item in queryset:
            try:
                client.sync_existing_instance(item)
                success_count += 1
            except Exception:
                fail_count += 1
        
        if success_count:
            messages.success(request, f"اطلاعات {success_count} سریال با موفقیت از TMDB به‌روزرسانی شد.")
        if fail_count:
            messages.error(request, f"بروزرسانی {fail_count} سریال با خطا مواجه شد.")
    sync_from_tmdb.short_description = "بروزرسانی و همگام‌سازی اطلاعات از TMDB"



@admin.register(Season)
class SeasonAdmin(TranslationAdmin):
    list_display = ['series', 'season_number', 'name']
    search_fields = ['season_number', 'series__title']
    autocomplete_fields = ['series']
    list_filter = [SeriesSearchFilter]


class EpisodeVideoInline(admin.TabularInline):
    model = EpisodeVideo
    extra = 1


@admin.register(Episode)
class EpisodeAdmin(TranslationAdmin):
    list_display = ['episode_number', 'season']
    list_filter = [SeriesSearchFilter, SeasonSearchFilter]
    inlines = [EpisodeVideoInline]
    autocomplete_fields = ['season']
    search_fields = ['episode_number', 'season__series__title', 'description']


class MovieCollectionItemVideoInline(admin.TabularInline):
    model = MovieCollectionItemVideo
    extra = 1


@admin.register(MovieCollectionItem)
class MovieCollectionItemAdmin(TranslationAdmin):
    list_display = ['title', 'movie', 'part_number']
    list_filter = [MovieSearchFilter]
    inlines = [MovieCollectionItemVideoInline]
    autocomplete_fields = ['movie']
    search_fields = ['title', 'movie__title', 'description']


@admin.register(SeriesTrailer)
class SeriesTrailerAdmin(admin.ModelAdmin):
    list_display = ['id', 'series']
    list_filter = [SeriesSearchFilter]
    autocomplete_fields = ['series']
    search_fields = ['series__title']


@admin.register(MovieComment)
class MovieCommentAdmin(NotificationMarkReadMixin, admin.ModelAdmin):
    list_display = ['user', 'movie', 'parent', 'is_approved', 'created_at']
    list_filter = ['is_approved', MovieSearchFilter, 'created_at']
    actions = ['approve_comments']
    autocomplete_fields = ['movie']
    search_fields = ['text', 'user__username']
    readonly_fields = ['created_at']

    def approve_comments(self, request, queryset):
        queryset.update(is_approved=True)
    approve_comments.short_description = "تایید دیدگاه‌های انتخاب شده"


@admin.register(SeriesComment)
class SeriesCommentAdmin(NotificationMarkReadMixin, admin.ModelAdmin):
    list_display = ['user', 'series', 'parent', 'is_approved', 'created_at']
    list_filter = ['is_approved', SeriesSearchFilter, 'created_at']
    actions = ['approve_comments']
    autocomplete_fields = ['series']
    search_fields = ['text', 'user__username']
    readonly_fields = ['created_at']

    def approve_comments(self, request, queryset):
        queryset.update(is_approved=True)
    approve_comments.short_description = "تایید دیدگاه‌های انتخاب شده"


from django.utils.html import format_html
from .services.tmdb import TMDBClient

@admin.register(ContentIngestion)
class ContentIngestionAdmin(admin.ModelAdmin):
    list_display = ['imdb_id', 'content_type', 'status_badge', 'created_movie', 'created_series', 'created_at']
    list_filter = ['content_type', 'status', 'created_at']
    search_fields = ['imdb_id', 'error_log']
    readonly_fields = ['created_movie', 'created_series', 'error_log', 'created_at', 'updated_at']
    actions = ['reprocess_ingestion']

    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'processing': 'blue',
            'completed': 'green',
            'failed': 'red',
        }
        color = colors.get(obj.status, 'black')
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, obj.get_status_display())
    status_badge.short_description = "وضعیت پردازش"

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.status in ['pending', 'failed']:
            client = TMDBClient()
            try:
                client.ingest(obj)
                if "قبلاً در دیتابیس موجود بوده" in obj.error_log:
                    messages.info(request, obj.error_log)
                else:
                    messages.success(request, f"محتوا با موفقیت از TMDB دریافت و ذخیره گردید.")
            except Exception as e:
                messages.error(request, f"خطا در دریافت متادیتا: {str(e)}")


    def reprocess_ingestion(self, request, queryset):
        client = TMDBClient()
        success_count = 0
        fail_count = 0
        for obj in queryset:
            try:
                client.ingest(obj)
                success_count += 1
            except Exception:
                fail_count += 1
        
        if success_count:
            messages.success(request, f"{success_count} درخواست با موفقیت پردازش شد.")
        if fail_count:
            messages.error(request, f"{fail_count} درخواست با خطا مواجه شد.")
    reprocess_ingestion.short_description = "پردازش مجدد موارد انتخاب شده"

