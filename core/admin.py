from django.contrib import admin
from modeltranslation.admin import TranslationAdmin, TranslationTabularInline
from jalali_date.admin import ModelAdminJalaliMixin
from jalali_date import datetime2jalali
from .models import SiteLanguage, SiteSettings, HeaderSetting, HeaderMenuItem, FooterSetting, FooterMenuColumn1, FooterMenuColumn2, FooterSocialMedia, AdminNotification, UserTasteSettings, DashboardSetting, ProfileImage, SupportAvatar, NewsletterSubscriber, ActorsPageSetting, ArchivePageSetting, HomePageSetting, HomeTrailer

@admin.register(ArchivePageSetting)
class ArchivePageSettingAdmin(TranslationAdmin):
    list_display = ['movies_title', 'series_title']

    def has_add_permission(self, request):
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(ActorsPageSetting)
class ActorsPageSettingAdmin(TranslationAdmin):
    list_display = ['title', 'per_page']

    def has_add_permission(self, request):
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = ['email', 'is_active', 'get_created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['email']
    ordering = ['-created_at']

    @admin.display(description='تاریخ ثبت‌نام', ordering='created_at')
    def get_created_at(self, obj):
        if obj.created_at:
            return datetime2jalali(obj.created_at).strftime('%Y/%m/%d %H:%M')
        return "-"

@admin.register(SiteLanguage)
class SiteLanguageAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active', 'order']
    list_editable = ['is_active', 'order']
    search_fields = ['name', 'code']

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ['title']

    def has_add_permission(self, request):
        # Allow only one instance of SiteSettings
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)


class HeaderMenuItemInline(TranslationTabularInline):
    model = HeaderMenuItem
    extra = 3  # Start with 3 empty forms
    ordering = ('order',)


@admin.register(HeaderSetting)
class HeaderSettingAdmin(admin.ModelAdmin):  # HeaderSetting has no translatable fields on itself, but contains translatable inline items.
    inlines = [HeaderMenuItemInline]

    def has_add_permission(self, request):
        # Allow only one instance of HeaderSetting
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)


class FooterMenuColumn1Inline(TranslationTabularInline):
    model = FooterMenuColumn1
    extra = 3
    ordering = ('order',)


class FooterMenuColumn2Inline(TranslationTabularInline):
    model = FooterMenuColumn2
    extra = 3
    ordering = ('order',)


class FooterSocialMediaInline(admin.TabularInline):
    model = FooterSocialMedia
    extra = 3
    ordering = ('order',)


@admin.register(FooterSetting)
class FooterSettingAdmin(TranslationAdmin):
    inlines = [FooterMenuColumn1Inline, FooterMenuColumn2Inline, FooterSocialMediaInline]

    def has_add_permission(self, request):
        # Allow only one instance of FooterSetting
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)


@admin.register(AdminNotification)
class AdminNotificationAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = ['message', 'is_read', 'get_created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['message']

    @admin.display(description='تاریخ ایجاد', ordering='created_at')
    def get_created_at(self, obj):
        if obj.created_at:
            return datetime2jalali(obj.created_at).strftime('%Y/%m/%d %H:%M')
        return "-"

@admin.register(UserTasteSettings)
class UserTasteSettingsAdmin(TranslationAdmin):
    list_display = ('title',)
    filter_horizontal = ('movies', 'series')

    def has_add_permission(self, request):
        if self.model.objects.count() >= 1:
            return False
        return super().has_add_permission(request)

class ProfileImageInline(admin.TabularInline):
    model = ProfileImage
    extra = 4
    ordering = ('order',)

class SupportAvatarInline(admin.TabularInline):
    model = SupportAvatar
    extra = 3
    ordering = ('order',)

@admin.register(DashboardSetting)
class DashboardSettingAdmin(TranslationAdmin):
    inlines = [ProfileImageInline, SupportAvatarInline]
    fields = ('vat_notice', 'support_phone', 'crypto_wallet_address', 'crypto_instructions')

    def has_add_permission(self, request):
        if self.model.objects.count() >= 1:
            return False
        return super().has_add_permission(request)


class HomeTrailerInline(admin.TabularInline):
    model = HomeTrailer
    extra = 1
    ordering = ('order',)


@admin.register(HomePageSetting)
class HomePageSettingAdmin(TranslationAdmin):
    inlines = [HomeTrailerInline]
    filter_horizontal = (
        'hero_movies',
        'hero_series',
        'halfprice_movies',
        'halfprice_series',
        'suggested_series',
        'featured_actors',
    )

    def has_add_permission(self, request):
        if self.model.objects.count() >= 1:
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False

