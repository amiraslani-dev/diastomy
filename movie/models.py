from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

class Person(models.Model):
    name = models.CharField(max_length=255, verbose_name="نام")
    slug = models.SlugField(max_length=255, unique=True, verbose_name="اسلاگ")
    bio = models.TextField(blank=True, verbose_name="بیوگرافی")
    photo = models.ImageField(upload_to='persons/', blank=True, null=True, verbose_name="تصویر")

    is_actor = models.BooleanField(default=True, verbose_name="بازیگر است")
    is_director = models.BooleanField(default=False, verbose_name="کارگردان است")

    class Meta:
        verbose_name = "شخص (بازیگر/کارگردان)"
        verbose_name_plural = "اشخاص (بازیگران/کارگردانان)"

    def __str__(self):
        role = ""
        if self.is_actor and self.is_director:
            role = " (بازیگر و کارگردان)"
        elif self.is_actor:
            role = " (بازیگر)"
        elif self.is_director:
            role = " (کارگردان)"
        return f"{self.name}{role}"


class Country(models.Model):
    name = models.CharField(max_length=100, verbose_name="نام کشور")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="اسلاگ")

    class Meta:
        verbose_name = "کشور"
        verbose_name_plural = "کشورها"

    def __str__(self):
        return self.name


class Genre(models.Model):
    name = models.CharField(max_length=100, verbose_name="نام ژانر")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="اسلاگ")

    class Meta:
        verbose_name = "ژانر"
        verbose_name_plural = "ژانرها"

    def __str__(self):
        return self.name


class Quality(models.Model):
    title = models.CharField(max_length=50, verbose_name="کیفیت (مثلا 1080p)")
    weight = models.PositiveIntegerField(default=0, help_text="وزن جهت ترتیب کیفیت‌ها (مثلا برای ۱۰۸۰ وزن ۱۰ و برای ۷۲۰ وزن ۸)", verbose_name="وزن ترتیب")

    class Meta:
        verbose_name = "کیفیت"
        verbose_name_plural = "کیفیت‌ها"
        ordering = ['-weight']

    def __str__(self):
        return self.title


class MovieBase(models.Model):
    title = models.CharField(max_length=255, verbose_name="عنوان")
    english_title_primary = models.CharField(max_length=255, verbose_name="بخش اول عنوان انگلیسی (رنگی)", blank=True)
    english_title_secondary = models.CharField(max_length=255, verbose_name="بخش دوم عنوان انگلیسی (سفید)", blank=True)
    slug = models.SlugField(max_length=255, unique=True, verbose_name="اسلاگ")
    description = models.TextField(verbose_name="توضیحات / خلاصه داستان")
    age_limit = models.PositiveIntegerField(default=0, verbose_name="رده سنی")
    production_year = models.PositiveIntegerField(null=True, blank=True, verbose_name="سال تولید")

    genres = models.ManyToManyField(Genre, related_name='%(class)s_genres', verbose_name="ژانرها")
    actors = models.ManyToManyField(Person, related_name='%(class)s_actors', verbose_name="بازیگران")
    director = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_directed',
        verbose_name="کارگردان"
    )
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="کشور سازنده")

    cover = models.ImageField(upload_to='covers/', verbose_name="تصویر کاور (پوستر)")
    banner = models.ImageField(upload_to='banners/', blank=True, null=True, verbose_name="تصویر بنر (دسکتاپ)")
    banner_mobile = models.ImageField(upload_to='banners_mobile/', blank=True, null=True, verbose_name="تصویر بنر (موبایل)")
    screenshot_1 = models.ImageField(upload_to='screenshots/', blank=True, null=True, verbose_name="اسکرین‌شات ۱")
    screenshot_2 = models.ImageField(upload_to='screenshots/', blank=True, null=True, verbose_name="اسکرین‌شات ۲")

    imdb_rating = models.FloatField(null=True, blank=True, verbose_name="امتیاز IMDb")
    satisfaction_rate = models.PositiveIntegerField(default=100, verbose_name="درصد رضایت کاربران")
    views_count = models.PositiveIntegerField(default=0, verbose_name="تعداد بازدید")

    seo_title = models.CharField(max_length=255, blank=True, verbose_name="عنوان سئو")
    meta_description = models.TextField(blank=True, verbose_name="توضیحات متا سئو")

    highest_quality = models.ForeignKey(Quality, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="بالاترین کیفیت موجود")

    teaser = models.FileField(upload_to='teasers/', blank=True, null=True, verbose_name="فایل تیزر")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")

    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='%(class)s_likes', blank=True, verbose_name="لایک‌ها")
    bookmarks = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='%(class)s_bookmarks', blank=True, verbose_name="ذخیره‌شده‌ها (Save)")
    class Meta:
        abstract = True

    def __str__(self):
        return self.title

    @property
    def approved_comments_count(self):
        return self.comments.filter(is_approved=True).count()


class Movie(MovieBase):
    class Meta:
        verbose_name = "فیلم"
        verbose_name_plural = "فیلم‌ها"

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('movie:movie_detail', kwargs={'slug': self.slug})


class Series(MovieBase):
    class Meta:
        verbose_name = "سریال"
        verbose_name_plural = "سریال‌ها"

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('movie:series_detail', kwargs={'slug': self.slug})


class Season(models.Model):
    series = models.ForeignKey(Series, on_delete=models.CASCADE, related_name='seasons', verbose_name="سریال")
    season_number = models.PositiveIntegerField(verbose_name="شماره فصل")
    title = models.CharField(max_length=255, blank=True, verbose_name="عنوان فصل")

    class Meta:
        verbose_name = "فصل"
        verbose_name_plural = "فصل‌ها"

    @property
    def name(self):
        # If there's a custom title entered by the admin for the current language, use it!
        if self.title:
            return self.title
        
        # Use Django standard translation keys
        from django.utils.translation import gettext as _
        
        ordinals = {
            1: _("First Season"),
            2: _("Second Season"),
            3: _("Third Season"),
            4: _("Fourth Season"),
            5: _("Fifth Season"),
            6: _("Sixth Season"),
            7: _("Seventh Season"),
            8: _("Eighth Season"),
            9: _("Ninth Season"),
            10: _("Tenth Season"),
        }
        
        if self.season_number in ordinals:
            return ordinals[self.season_number]
        
        # Fallback for higher numbers (e.g. 11+): "Season 11"
        return _("Season %(number)s") % {'number': self.season_number}

    def __str__(self):
        return f"{self.series.title} - {self.name}"


class Episode(models.Model):
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name='episodes', verbose_name="فصل")
    episode_number = models.PositiveIntegerField(verbose_name="شماره قسمت")
    duration = models.PositiveIntegerField(help_text="مدت زمان به ثانیه", null=True, blank=True, verbose_name="مدت زمان")
    description = models.TextField(blank=True, verbose_name="توضیحات قسمت")
    satisfaction_rate = models.PositiveIntegerField(default=100, verbose_name="درصد رضایت")

    class Meta:
        verbose_name = "قسمت"
        verbose_name_plural = "قسمت‌ها"

    def __str__(self):
        return f"{self.season.series.title} - {self.season.name} - قسمت {self.episode_number}"


class EpisodeVideo(models.Model):
    episode = models.ForeignKey(Episode, on_delete=models.CASCADE, related_name='videos', verbose_name="قسمت")
    quality = models.ForeignKey(Quality, on_delete=models.CASCADE, verbose_name="کیفیت")
    video = models.FileField(upload_to='videos/', verbose_name="فایل ویدیو")
    
    subtitle = models.FileField(upload_to='subtitles/', blank=True, null=True, verbose_name="فایل زیرنویس (.vtt یا .srt)")
    subtitle_label = models.CharField(max_length=100, blank=True, verbose_name="برچسب زیرنویس (مثلا فارسی)")
    subtitle_srclang = models.CharField(max_length=10, blank=True, verbose_name="کد زبان زیرنویس (مثلا fa)")

    class Meta:
        verbose_name = "ویدیو قسمت"
        verbose_name_plural = "ویدیوهای قسمت‌ها"

    def __str__(self):
        return f"{self.episode} - {self.quality.title}"


class MovieVideo(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='videos', verbose_name="فیلم")
    quality = models.ForeignKey(Quality, on_delete=models.CASCADE, verbose_name="کیفیت")
    video = models.FileField(upload_to='videos/', verbose_name="فایل ویدیو")

    subtitle = models.FileField(upload_to='subtitles/', blank=True, null=True, verbose_name="فایل زیرنویس (.vtt یا .srt)")
    subtitle_label = models.CharField(max_length=100, blank=True, verbose_name="برچسب زیرنویس (مثلا فارسی)")
    subtitle_srclang = models.CharField(max_length=10, blank=True, verbose_name="کد زبان زیرنویس (مثلا fa)")

    class Meta:
        verbose_name = "ویدیو فیلم"
        verbose_name_plural = "ویدیوهای فیلم‌ها"

    def __str__(self):
        return f"{self.movie.title} - {self.quality.title}"


class MovieCollectionItem(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='collection_items', verbose_name="فیلم اصلی")
    title = models.CharField(max_length=255, verbose_name="عنوان پارت")
    description = models.TextField(blank=True, verbose_name="توضیحات پارت")
    cover = models.ImageField(upload_to='collection_covers/', blank=True, null=True, verbose_name="کاور پارت")
    part_number = models.PositiveIntegerField(default=1, verbose_name="شماره پارت")
    duration = models.PositiveIntegerField(help_text="مدت زمان به ثانیه", null=True, blank=True, verbose_name="مدت زمان")

    class Meta:
        verbose_name = "آیتم کالکشن فیلم"
        verbose_name_plural = "آیتم‌های کالکشن فیلم"
        ordering = ['part_number']

    def __str__(self):
        return f"{self.movie.title} - پارت {self.part_number}: {self.title}"


class MovieCollectionItemVideo(models.Model):
    collection_item = models.ForeignKey(MovieCollectionItem, on_delete=models.CASCADE, related_name='videos', verbose_name="آیتم کالکشن")
    quality = models.ForeignKey(Quality, on_delete=models.CASCADE, verbose_name="کیفیت")
    video = models.FileField(upload_to='videos/', verbose_name="فایل ویدیو")

    subtitle = models.FileField(upload_to='subtitles/', blank=True, null=True, verbose_name="فایل زیرنویس (.vtt یا .srt)")
    subtitle_label = models.CharField(max_length=100, blank=True, verbose_name="برچسب زیرنویس (مثلا فارسی)")
    subtitle_srclang = models.CharField(max_length=10, blank=True, verbose_name="کد زبان زیرنویس (مثلا fa)")

    class Meta:
        verbose_name = "ویدیو آیتم کالکشن"
        verbose_name_plural = "ویدیوهای آیتم‌های کالکشن"

    def __str__(self):
        return f"{self.collection_item.title} - {self.quality.title}"


class SeriesTrailer(models.Model):
    series = models.ForeignKey(Series, on_delete=models.CASCADE, related_name='trailers', verbose_name="سریال")
    video = models.FileField(upload_to='trailers/', verbose_name="فایل تریلر")

    class Meta:
        verbose_name = "تریلر سریال"
        verbose_name_plural = "تریلرهای سریال‌ها"

    def __str__(self):
        return f"تریلر {self.series.title}"


class MovieComment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="کاربر")
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='comments', verbose_name="فیلم")
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies', verbose_name="پاسخ به")
    text = models.TextField(verbose_name="متن نظر")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")
    is_approved = models.BooleanField(default=False, verbose_name="تایید شده")
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='movie_comment_likes', blank=True, verbose_name="لایک‌ها")
    dislikes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='movie_comment_dislikes', blank=True, verbose_name="دیس‌لایک‌ها")

    class Meta:
        verbose_name = "دیدگاه فیلم"
        verbose_name_plural = "دیدگاه‌های فیلم‌ها"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.movie.title}"


class SeriesComment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="کاربر")
    series = models.ForeignKey(Series, on_delete=models.CASCADE, related_name='comments', verbose_name="سریال")
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies', verbose_name="پاسخ به")
    text = models.TextField(verbose_name="متن نظر")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")
    is_approved = models.BooleanField(default=False, verbose_name="تایید شده")
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='series_comment_likes', blank=True, verbose_name="لایک‌ها")
    dislikes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='series_comment_dislikes', blank=True, verbose_name="دیس‌لایک‌ها")

    class Meta:
        verbose_name = "دیدگاه سریال"
        verbose_name_plural = "دیدگاه‌های سریال‌ها"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.series.title}"


# Signals to automatically trigger notifications on comments creation using centralized AdminNotification
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.dispatch import receiver
from core.models import AdminNotification

@receiver(post_save, sender=MovieComment)
def create_movie_comment_notification(sender, instance, created, **kwargs):
    if created:
        ct = ContentType.objects.get_for_model(instance)
        AdminNotification.objects.create(
            content_type=ct,
            object_id=instance.id,
            message=f"دیدگاه جدید برای فیلم «{instance.movie.title_fa}» توسط {instance.user.username}"
        )


@receiver(post_save, sender=SeriesComment)
def create_series_comment_notification(sender, instance, created, **kwargs):
    if created:
        ct = ContentType.objects.get_for_model(instance)
        AdminNotification.objects.create(
            content_type=ct,
            object_id=instance.id,
            message=f"دیدگاه جدید برای سریال «{instance.series.title_fa}» توسط {instance.user.username}"
        )
