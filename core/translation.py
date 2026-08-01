from modeltranslation.translator import register, TranslationOptions
from .models import HeaderMenuItem, FooterSetting, FooterMenuColumn1, FooterMenuColumn2, UserTasteSettings

@register(HeaderMenuItem)
class HeaderMenuItemTranslationOptions(TranslationOptions):
    fields = ('title', 'link')


@register(FooterSetting)
class FooterSettingTranslationOptions(TranslationOptions):
    fields = (
        'col1_title_mobile',
        'col2_title_mobile',
        'footer_text',
        'newsletter_title_desktop',
        'newsletter_title_mobile',
        'privacy_text',
    )


@register(FooterMenuColumn1)
class FooterMenuColumn1TranslationOptions(TranslationOptions):
    fields = ('title', 'link')


@register(FooterMenuColumn2)
class FooterMenuColumn2TranslationOptions(TranslationOptions):
    fields = ('title', 'link')

@register(UserTasteSettings)
class UserTasteSettingsTranslationOptions(TranslationOptions):
    fields = ('title',)

from .models import DashboardSetting, ActorsPageSetting, ArchivePageSetting, HomePageSetting

@register(DashboardSetting)
class DashboardSettingTranslationOptions(TranslationOptions):
    fields = ('vat_notice', 'crypto_instructions')

@register(ActorsPageSetting)
class ActorsPageSettingTranslationOptions(TranslationOptions):
    fields = ('title', 'meta_description')

@register(ArchivePageSetting)
class ArchivePageSettingTranslationOptions(TranslationOptions):
    fields = ('movies_title', 'movies_meta_description', 'series_title', 'series_meta_description')

@register(HomePageSetting)
class HomePageSettingTranslationOptions(TranslationOptions):
    fields = ('title', 'banner_title', 'banner_description', 'banner_button_text', 'banner_button_link')

