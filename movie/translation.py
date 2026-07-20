from modeltranslation.translator import register, TranslationOptions
from .models import Country, Genre, Person, Movie, Series, MovieCollectionItem, Season, Episode

@register(Country)
class CountryTranslationOptions(TranslationOptions):
    fields = ('name',)


@register(Genre)
class GenreTranslationOptions(TranslationOptions):
    fields = ('name',)


@register(Person)
class PersonTranslationOptions(TranslationOptions):
    fields = ('bio',)


@register(Movie)
class MovieTranslationOptions(TranslationOptions):
    fields = (
        'title',
        'description',
        'seo_title',
        'meta_description',
    )


@register(Series)
class SeriesTranslationOptions(TranslationOptions):
    fields = (
        'title',
        'description',
        'seo_title',
        'meta_description',
    )


@register(MovieCollectionItem)
class MovieCollectionItemTranslationOptions(TranslationOptions):
    fields = ('title', 'description')


@register(Season)
class SeasonTranslationOptions(TranslationOptions):
    fields = ('title',)


@register(Episode)
class EpisodeTranslationOptions(TranslationOptions):
    fields = ('description',)
