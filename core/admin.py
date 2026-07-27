from django.contrib import admin
from modeltranslation.admin import TranslationAdmin, TranslationTabularInline
from .models import SiteLanguage, SiteSettings, HeaderSetting, HeaderMenuItem, FooterSetting, FooterMenuColumn1, FooterMenuColumn2, FooterSocialMedia, AdminNotification, UserTasteSettings, DashboardSetting, ProfileImage, SupportAvatar

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
class AdminNotificationAdmin(admin.ModelAdmin):
    list_display = ['message', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['message']

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
class DashboardSettingAdmin(admin.ModelAdmin):
    inlines = [ProfileImageInline, SupportAvatarInline]

    def has_add_permission(self, request):
        if self.model.objects.count() >= 1:
            return False
        return super().has_add_permission(request)
