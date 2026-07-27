from django.db import migrations


def populate_languages(apps, schema_editor):
    SiteLanguage = apps.get_model('core', 'SiteLanguage')
    languages = [
        {'code': 'fa', 'name': 'فارسی', 'is_active': True, 'order': 1},
        {'code': 'en', 'name': 'English', 'is_active': True, 'order': 2},
        {'code': 'ar', 'name': 'العربیه', 'is_active': True, 'order': 3},
        {'code': 'ru', 'name': 'Русский', 'is_active': True, 'order': 4},
        {'code': 'tr', 'name': 'Türkçe', 'is_active': True, 'order': 5},
    ]
    for lang in languages:
        SiteLanguage.objects.get_or_create(
            code=lang['code'],
            defaults={
                'name': lang['name'],
                'is_active': lang['is_active'],
                'order': lang['order']
            }
        )


def reverse_populate(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_sitelanguage_footermenucolumn1_link_ru_and_more'),
    ]

    operations = [
        migrations.RunPython(populate_languages, reverse_populate),
    ]
