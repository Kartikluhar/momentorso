from datetime import timedelta
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Profile(models.Model):
    """
    User profile model extending the default Django User.
    Handles role-based access for admins.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    ROLE_CHOICES = (
        ('sadmin','Super admin'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='admin')
    def __str__(self):
        return self.user.username

class Inquiry(models.Model):
    """
    Stores contact inquiries submitted by users from the frontend.
    """
    name = models.CharField(max_length=100, null=False, blank=False)
    email = models.EmailField(null=False, blank=False)
    mobile = models.CharField(max_length=20, null=False, blank=False)
    message = models.TextField(null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Category(models.Model):
    """
    Represents a category/album for the gallery, containing multiple images.
    """
    image = models.ImageField(upload_to='category/', null=False, blank=False)
    title = models.CharField(max_length=100, null=False, blank=False, unique=True)
    description = models.TextField(null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Image(models.Model):
    """
    Individual images uploaded to a specific gallery category.
    """
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='images/', null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.category.title


class StoryQuerySet(models.QuerySet):
    """
    QuerySet providing filtered access to active stories.
    A story is active only while it is published and its expiration timestamp
    is strictly in the future.
    """
    def active(self):
        now = timezone.now()
        return self.filter(
            models.Q(status='published', published_at__lte=now, expires_at__gt=now) |
            models.Q(status='scheduled', scheduled_at__lte=now, expires_at__gt=now)
        ).order_by('-published_at', '-created_at')


class Story(models.Model):
    """
    Represents an Instagram-style story for announcements, festival posters,
    events, and promotions that automatically expire 24 hours after publication.
    """
    CATEGORY_CHOICES = (
        ('announcement', 'Announcement'),
        ('festival', 'Festival'),
        ('event', 'Event'),
        ('general', 'General'),
    )
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('scheduled', 'Scheduled'),
    )

    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='stories/')
    description = models.TextField(blank=True, default='')
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='general')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    scheduled_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='stories')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = StoryQuerySet.as_manager()

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Story'
        verbose_name_plural = 'Stories'

    def __str__(self):
        return f"{self.title} ({self.get_category_display()})"

    @classmethod
    def get_active_stories(cls):
        return cls.objects.active()

    @property
    def is_active(self):
        now = timezone.now()
        if self.status == 'published':
            return bool(self.published_at and self.published_at <= now and self.expires_at and self.expires_at > now)
        elif self.status == 'scheduled':
            return bool(self.scheduled_at and self.scheduled_at <= now and self.expires_at and self.expires_at > now)
        return False

    @property
    def is_expired(self):
        if not self.expires_at:
            return False
        return timezone.now() >= self.expires_at

    @property
    def computed_status(self):
        now = timezone.now()
        if self.status == 'draft':
            return 'draft'
        if self.status == 'scheduled':
            if self.scheduled_at and self.scheduled_at > now:
                return 'scheduled'
            elif self.expires_at and now >= self.expires_at:
                return 'expired'
            return 'active'
        if self.status == 'published':
            if self.expires_at and now >= self.expires_at:
                return 'expired'
            if self.published_at and self.published_at > now:
                return 'scheduled'
            return 'active'
        return self.status

    @property
    def time_remaining_display(self):
        """Human-readable time remaining before expiration."""
        if not self.is_active or not self.expires_at:
            return None
        diff = self.expires_at - timezone.now()
        total_seconds = int(diff.total_seconds())
        if total_seconds <= 0:
            return "Expired"
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        if hours > 0:
            return f"{hours}h {minutes}m left"
        return f"{minutes}m left"

    @property
    def time_remaining_seconds(self):
        if not self.is_active or not self.expires_at:
            return 0
        diff = self.expires_at - timezone.now()
        return max(0, int(diff.total_seconds()))

    def publish(self, save=True):
        """
        Publish or republish story, setting its publication timestamp to now
        and expiration timestamp to exactly 24 hours from now.
        """
        now = timezone.now()
        self.status = 'published'
        self.published_at = now
        self.expires_at = now + timedelta(hours=24)
        if save:
            self.save()

    def unpublish(self, save=True):
        """Immediately unpublish story so it is excluded from public display."""
        self.status = 'draft'
        if save:
            self.save()

    def save(self, *args, **kwargs):
        # Auto-compute timestamps on initial publish if not set
        if self.status == 'published':
            if not self.published_at or not self.expires_at:
                now = timezone.now()
                self.published_at = now
                self.expires_at = now + timedelta(hours=24)
        elif self.status == 'scheduled':
            if self.scheduled_at and not self.expires_at:
                self.published_at = self.scheduled_at
                self.expires_at = self.scheduled_at + timedelta(hours=24)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.image:
            self.image.delete(save=False)
        super().delete(*args, **kwargs)