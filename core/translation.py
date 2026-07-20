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
