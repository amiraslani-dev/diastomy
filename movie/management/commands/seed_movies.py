import os
from django.core.management.base import BaseCommand
from movie.models import (
    Person, Country, Genre, Quality, Movie, Series, Season, Episode,
    EpisodeVideo, MovieVideo, MovieCollectionItem, MovieCollectionItemVideo, SeriesTrailer, MovieComment, SeriesComment
)
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds the database with at least 30 instances per model for advanced testing'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Cleaning up existing movie database...'))

        # Clear existing database records
        MovieComment.objects.all().delete()
        SeriesComment.objects.all().delete()
        MovieCollectionItemVideo.objects.all().delete()
        MovieCollectionItem.objects.all().delete()
        EpisodeVideo.objects.all().delete()
        Episode.objects.all().delete()
        Season.objects.all().delete()
        SeriesTrailer.objects.all().delete()
        MovieVideo.objects.all().delete()
        Movie.objects.all().delete()
        Series.objects.all().delete()
        Person.objects.all().delete()
        Country.objects.all().delete()
        Genre.objects.all().delete()
        Quality.objects.all().delete()

        # Dummy media content files for testing
        gif_data = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x4c\x01\x00\x3b'
        cover_file = ContentFile(gif_data, name='test_cover.gif')
        banner_file = ContentFile(gif_data, name='test_banner.gif')
        banner_mobile_file = ContentFile(gif_data, name='test_banner_mobile.gif')
        screenshot_file = ContentFile(gif_data, name='test_screenshot.gif')
        video_file = ContentFile(b'dummy video contents', name='test_video.mp4')
        subtitle_file = ContentFile(b'1\n00:00:01,000 --> 00:00:05,000\nSub.', name='test_sub.srt')

        # 1. Seed 5 Qualities
        q1080 = Quality.objects.create(title="1080p", weight=10)
        q720 = Quality.objects.create(title="720p", weight=8)
        q480 = Quality.objects.create(title="480p", weight=5)
        q360 = Quality.objects.create(title="360p", weight=3)
        q4k = Quality.objects.create(title="4K Ultra HD", weight=15)
        self.stdout.write(self.style.SUCCESS('- Seeded Qualities'))

        # 2. Seed 30 Countries
        countries_data = [
            ("ایران", "Iran", "إيران"),
            ("آمریکا", "USA", "أمريكا"),
            ("اسپانیا", "Spain", "إسبانيا"),
            ("انگلستان", "UK", "المملكة المتحدة"),
            ("فرانسه", "France", "فرنسا"),
            ("آلمان", "Germany", "ألمانيا"),
            ("ایتالیا", "Italy", "إيطاليا"),
            ("ژاپن", "Japan", "اليابان"),
            ("کره جنوبی", "South Korea", "كوريا الجنوبية"),
            ("کانادا", "Canada", "كندا"),
            ("استرالیا", "Australia", "أرستوراليا"),
            ("هند", "India", "الهند"),
            ("ترکیه", "Turkey", "تركيا"),
            ("برزیل", "Brazil", "البرازيل"),
            ("روسیه", "Russia", "روسيا"),
            ("چین", "China", "الصين"),
            ("مصر", "Egypt", "مصر"),
            ("سوئد", "Sweden", "السويد"),
            ("دانمارک", "Denmark", "الدانمرك"),
            ("هلند", "Netherlands", "هولندا"),
            ("مکزیک", "Mexico", "المكسيك"),
            ("آرژانتین", "Argentina", "الأرجنتين"),
            ("نروژ", "Norway", "النرويج"),
            ("فنلاند", "Finland", "فنلندا"),
            ("لهستان", "Poland", "بولندا"),
            ("یونان", "Greece", "اليونان"),
            ("اتریش", "Austria", "النمسا"),
            ("سوئیس", "Switzerland", "سويسرا"),
            ("بلژیک", "Belgium", "بلجيكا"),
            ("آفریقای جنوبی", "South Africa", "جنوب أفريقيا"),
        ]
        countries = []
        for fa, en, ar in countries_data:
            countries.append(Country.objects.create(
                name_fa=fa, name_en=en, name_ar=ar,
                slug=en.lower().replace(" ", "-")
            ))
        self.stdout.write(self.style.SUCCESS('- Seeded 30 Countries'))

        # 3. Seed 30 Genres
        genres_data = [
            ("اکشن", "Action", "أكشن"),
            ("درام", "Drama", "دراما"),
            ("هیجان انگیز", "Thriller", "إثارة"),
            ("کمدی", "Comedy", "كوميديا"),
            ("علمی تخیلی", "Sci-Fi", "خيال علمي"),
            ("وحشت", "Horror", "رعب"),
            ("ماجراجویی", "Adventure", "مغامرة"),
            ("عاشقانه", "Romance", "رومانسية"),
            ("فانتزی", "Fantasy", "فانتازيا"),
            ("مستند", "Documentary", "وثائقي"),
            ("جنایی", "Crime", "جريمة"),
            ("رازآلود", "Mystery", "غموض"),
            ("تاریخی", "History", "تاريخي"),
            ("جنگی", "War", "حربي"),
            ("ورزشی", "Sport", "رياضي"),
            ("انیمیشن", "Animation", "رسوم متحركة"),
            ("بیوگرافی", "Biography", "سيرة ذاتية"),
            ("موزیکال", "Musical", "موسيقي"),
            ("خانوادگی", "Family", "عائلي"),
            ("وسترن", "Western", "غربي"),
            ("ابرقهرمانی", "Superhero", "بطل خارق"),
            ("تراژدی", "Tragedy", "مأساة"),
            ("نوآر", "Noir", "نوار"),
            ("آخرالزمانی", "Apocalyptic", "رؤيوي"),
            ("حماسی", "Epic", "ملحمي"),
            ("روانشناختی", "Psychological", "نفسي"),
            ("کارآگاهی", "Detective", "تحري"),
            ("تخیلی", "Fiction", "خيال"),
            ("ماوراء طبیعی", "Supernatural", "خارق للطبيعة"),
            ("نوجوانان", "Teen", "شبابي"),
        ]
        genres = []
        for fa, en, ar in genres_data:
            genres.append(Genre.objects.create(
                name_fa=fa, name_en=en, name_ar=ar,
                slug=en.lower().replace(" ", "-").replace("/", "-")
            ))
        self.stdout.write(self.style.SUCCESS('- Seeded 30 Genres'))

        # 4. Seed 35 Persons (Actors & Directors)
        persons = []
        for i in range(1, 36):
            is_actor = (i % 3 != 0)
            is_director = (i % 2 == 0)
            persons.append(Person.objects.create(
                name_fa=f"هنرمند تستی {i}", name_en=f"Test Artist {i}", name_ar=f"فنان تجريبي {i}",
                slug=f"test-artist-{i}", is_actor=is_actor, is_director=is_director,
                bio_fa=f"بیوگرافی کامل هنرمند شماره {i} جهت تست داده‌ها در مدیریت."
            ))
        self.stdout.write(self.style.SUCCESS('- Seeded 35 Persons (Actors/Directors)'))

        # 5. Seed 30 Movies
        movies = []
        for i in range(1, 31):
            movie = Movie.objects.create(
                title_fa=f"فیلم تستی {i}", title_en=f"Test Movie {i}", title_ar=f"فيلم تجريبي {i}",
                english_title_primary=f"Movie {i}", english_title_secondary="Special Edition" if i % 2 == 0 else "",
                slug=f"test-movie-{i}",
                description_fa=f"توضیحات و داستان مربوط به فیلم سینمایی تستی شماره {i} جهت بررسی ساختار فیلترها و تست صفحات سایت.",
                description_en=f"This is the english description details for test movie number {i}.",
                description_ar=f"هذا هو وصف التفاصيل للفيلم التجريبي رقم {i}.",
                age_limit=13 if i % 2 == 0 else 18,
                country=countries[i % len(countries)],
                cover=cover_file,
                banner=banner_file,
                banner_mobile=banner_mobile_file,
                screenshot_1=screenshot_file,
                screenshot_2=screenshot_file,
                imdb_rating=5.5 + (i % 5) * 0.8,
                highest_quality=q1080 if i % 2 == 0 else q720,
                seo_title_fa=f"دانلود فیلم سینمایی فیلم تستی {i} با لینک مستقیم",
                meta_description_fa=f"دانلود کامل فیلم تستی {i} با زیرنویس فارسی.",
                teaser=video_file
            )
            movie.genres.add(genres[i % len(genres)], genres[(i + 1) % len(genres)])
            movie.actors.add(persons[i % len(persons)], persons[(i + 2) % len(persons)])
            
            directors = [p for p in persons if p.is_director]
            if directors:
                movie.director = directors[i % len(directors)]
            movie.save()

            # Movie Quality Videos
            MovieVideo.objects.create(movie=movie, quality=q1080, video=video_file, subtitle=subtitle_file, subtitle_label="فارسی", subtitle_srclang="fa")
            MovieVideo.objects.create(movie=movie, quality=q720, video=video_file)
            movies.append(movie)
        self.stdout.write(self.style.SUCCESS('- Seeded 30 Movies and MovieVideos'))

        # 6. Seed 30 Movie Collection Items (Cinematic Parts)
        for m_idx in range(5):
            target_movie = movies[m_idx]
            for p_idx in range(1, 7):
                part = MovieCollectionItem.objects.create(
                    movie=target_movie, part_number=p_idx, duration=3000 + p_idx * 150,
                    title_fa=f"پارت {p_idx} از کالکشن {target_movie.title_fa}",
                    title_en=f"Part {p_idx} of Collection {target_movie.title_en}",
                    title_ar=f"الجزء {p_idx} من {target_movie.title_ar}",
                    description_fa=f"توضیحات تستی برای پارت {p_idx} مربوط به کالکشن این فیلم.",
                    cover=cover_file
                )
                MovieCollectionItemVideo.objects.create(collection_item=part, quality=q1080, video=video_file)
        self.stdout.write(self.style.SUCCESS('- Seeded 30 MovieCollectionItems'))

        # 7. Seed 30 Series
        series_list = []
        for i in range(1, 31):
            series = Series.objects.create(
                title_fa=f"سریال تستی {i}", title_en=f"Test Series {i}", title_ar=f"مسلسل تجريبي {i}",
                english_title_primary=f"Series {i}", english_title_secondary="Season One" if i % 2 == 0 else "",
                slug=f"test-series-{i}",
                description_fa=f"توضیحات و داستان مربوط به سریال تلویزیونی تستی شماره {i} جهت بررسی ساختار فیلترها و تست صفحات سایت.",
                description_en=f"This is the english description details for test series number {i}.",
                description_ar=f"هذا هو وصف التفاصيل للمسلسل التجريبي رقم {i}.",
                age_limit=15 if i % 2 == 0 else 18,
                country=countries[(i + 4) % len(countries)],
                cover=cover_file,
                banner=banner_file,
                banner_mobile=banner_mobile_file,
                screenshot_1=screenshot_file,
                screenshot_2=screenshot_file,
                imdb_rating=6.2 + (i % 4) * 0.7,
                highest_quality=q1080 if i % 2 == 0 else q720,
                seo_title_fa=f"دانلود سریال تستی {i} با لینک مستقیم",
                meta_description_fa=f"دانلود کامل سریال تستی {i} با زیرنویس فارسی.",
                teaser=video_file
            )
            series.genres.add(genres[i % len(genres)], genres[(i + 2) % len(genres)])
            series.actors.add(persons[i % len(persons)])
            
            directors = [p for p in persons if p.is_director]
            if directors:
                series.director = directors[(i + 1) % len(directors)]
            series.save()

            # Add 1 SeriesTrailer for each series (Total 30 trailers)
            SeriesTrailer.objects.create(series=series, video=video_file)
            series_list.append(series)
        self.stdout.write(self.style.SUCCESS('- Seeded 30 Series and 30 SeriesTrailers'))

        # 8. Seed 30 Seasons & 30 Episodes
        for i, series in enumerate(series_list):
            season = Season.objects.create(series=series, season_number=1, title_fa="فصل اول", title_en="Season 1")
            ep = Episode.objects.create(
                season=season, episode_number=1, duration=2700 + (i % 5) * 100,
                description_fa=f"توضیحات تستی قسمت اول از فصل اول سریال {series.title_fa} جهت درج در دیتابیس."
            )
            EpisodeVideo.objects.create(episode=ep, quality=q1080, video=video_file)
        self.stdout.write(self.style.SUCCESS('- Seeded 30 Seasons and 30 Episodes'))

        # 9. Seed 30 MovieComments & 30 SeriesComments
        admin_user = User.objects.filter(is_superuser=True).first()
        if admin_user:
            for i in range(1, 31):
                MovieComment.objects.create(
                    user=admin_user,
                    movie=movies[i % len(movies)],
                    text=f"دیدگاه تستی فیلم شماره {i} ثبت شده برای تست سیستم نظرات فیلم.",
                    is_approved=(i % 3 != 0)
                )
                SeriesComment.objects.create(
                    user=admin_user,
                    series=series_list[i % len(series_list)],
                    text=f"دیدگاه تستی سریال شماره {i} ثبت شده برای تست سیستم نظرات سریال.",
                    is_approved=(i % 3 != 0)
                )
            self.stdout.write(self.style.SUCCESS('- Seeded Comments (Movie & Series)'))

        self.stdout.write(self.style.SUCCESS('Successfully seeded movie app with at least 30 items per model!'))
