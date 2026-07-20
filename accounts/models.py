import random
from django.db import models
from django.contrib.auth.models import AbstractUser

def generate_user_number():
    while True:
        num = "".join([str(random.randint(0, 9)) for _ in range(10)])
        # Avoid starting with 0 if you want a clean number look, or allow it
        if num[0] != '0' and not User.objects.filter(user_number=num).exists():
            return num

class User(AbstractUser):
    phone = models.CharField(max_length=15, unique=True, null=True, blank=True, verbose_name="شماره موبایل")
    full_name = models.CharField(max_length=255, null=True, blank=True, verbose_name="نام و نام خانوادگی")
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, verbose_name="تصویر آواتار")
    user_number = models.CharField(max_length=10, unique=True, editable=False, verbose_name="شماره کاربری")
    
    # Onboarding fields
    has_completed_onboarding = models.BooleanField(default=False, verbose_name="تکمیل سلیقه‌سنجی")
    favorite_movies = models.ManyToManyField('movie.Movie', blank=True, verbose_name="فیلم‌های مورد علاقه")
    favorite_series = models.ManyToManyField('movie.Series', blank=True, verbose_name="سریال‌های مورد علاقه")
    def save(self, *args, **kwargs):
        if not self.user_number:
            self.user_number = generate_user_number()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username
