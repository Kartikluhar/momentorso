from datetime import timedelta
import io
from PIL import Image as PILImage
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone

from .models import Story, Category, Image as GalleryImage, Inquiry


def create_test_image(filename="test.jpg", ext="JPEG", size=(100, 100), color=(200, 160, 80)):
    """Helper to generate a real in-memory image for file upload testing."""
    file_io = io.BytesIO()
    image = PILImage.new("RGB", size, color)
    image.save(file_io, format=ext)
    file_io.seek(0)
    return SimpleUploadedFile(filename, file_io.read(), content_type=f"image/{ext.lower()}")


class StoryModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='admin_test', password='password123', is_staff=True)
        self.image = create_test_image("poster1.jpg")

    def test_story_published_expiration_exact_24h(self):
        """A published story must have its expiration set to exactly 24 hours after publication."""
        before = timezone.now()
        story = Story.objects.create(
            title="Grand Gala Festival",
            category="festival",
            status="published",
            image=self.image,
            created_by=self.user
        )
        after = timezone.now()

        self.assertIsNotNone(story.published_at)
        self.assertIsNotNone(story.expires_at)
        self.assertTrue(before <= story.published_at <= after)
        expected_expiry = story.published_at + timedelta(hours=24)
        self.assertEqual(story.expires_at, expected_expiry)
        self.assertTrue(story.is_active)
        self.assertFalse(story.is_expired)
        self.assertEqual(story.computed_status, 'active')

    def test_active_queryset_includes_published_non_expired(self):
        """Story.objects.active() must include published non-expired stories."""
        story = Story.objects.create(
            title="Active Announcement",
            category="announcement",
            status="published",
            image=self.image,
            created_by=self.user
        )
        active_stories = list(Story.objects.active())
        self.assertIn(story, active_stories)

    def test_active_queryset_excludes_expired_story(self):
        """Stories that have passed their 24h expiration must be excluded from active() without a cleanup job."""
        now = timezone.now()
        story = Story.objects.create(
            title="Expired Festival Story",
            category="festival",
            status="published",
            published_at=now - timedelta(hours=25),
            expires_at=now - timedelta(hours=1),
            image=self.image,
            created_by=self.user
        )
        # Directly check model properties
        self.assertTrue(story.is_expired)
        self.assertFalse(story.is_active)
        self.assertEqual(story.computed_status, 'expired')

        # Check queryset filtering
        active_stories = list(Story.objects.active())
        self.assertNotIn(story, active_stories)

    def test_active_queryset_excludes_draft_and_unpublished(self):
        """Draft stories must not appear in active queries."""
        story = Story.objects.create(
            title="Draft Story",
            category="general",
            status="draft",
            image=self.image,
            created_by=self.user
        )
        self.assertFalse(story.is_active)
        self.assertEqual(story.computed_status, 'draft')
        self.assertNotIn(story, Story.objects.active())

        # Now publish and then unpublish
        story.publish()
        self.assertTrue(story.is_active)
        self.assertIn(story, Story.objects.active())

        story.unpublish()
        self.assertFalse(story.is_active)
        self.assertEqual(story.status, 'draft')
        self.assertNotIn(story, Story.objects.active())

    def test_scheduled_story_lifecycle(self):
        """Scheduled stories are inactive before scheduled_at, active during the 24h window, and expired after."""
        now = timezone.now()
        # Future scheduled story
        future_dt = now + timedelta(hours=5)
        story = Story(
            title="Scheduled Exhibition",
            category="event",
            status="scheduled",
            scheduled_at=future_dt,
            image=self.image,
            created_by=self.user
        )
        story.save()

        self.assertFalse(story.is_active)
        self.assertEqual(story.computed_status, 'scheduled')
        self.assertNotIn(story, Story.objects.active())
        self.assertEqual(story.expires_at, future_dt + timedelta(hours=24))

        # Time arrives (scheduled_at in past by 2 hours, expiry in future by 22h)
        story.scheduled_at = now - timedelta(hours=2)
        story.published_at = story.scheduled_at
        story.expires_at = story.scheduled_at + timedelta(hours=24)
        story.save()

        self.assertTrue(story.is_active)
        self.assertEqual(story.computed_status, 'active')
        self.assertIn(story, Story.objects.active())

        # Time expires (scheduled_at 26 hours ago)
        story.scheduled_at = now - timedelta(hours=26)
        story.published_at = story.scheduled_at
        story.expires_at = story.scheduled_at + timedelta(hours=24)
        story.save()

        self.assertFalse(story.is_active)
        self.assertTrue(story.is_expired)
        self.assertEqual(story.computed_status, 'expired')
        self.assertNotIn(story, Story.objects.active())

    def test_republish_resets_24h_timer(self):
        """Republishing resets the published_at to now and extends expiration to exactly now + 24 hours."""
        now = timezone.now()
        # Start with an expired story
        story = Story.objects.create(
            title="To Be Republished",
            category="event",
            status="published",
            published_at=now - timedelta(hours=30),
            expires_at=now - timedelta(hours=6),
            image=self.image,
            created_by=self.user
        )
        self.assertTrue(story.is_expired)

        # Republish
        republish_time = timezone.now()
        story.publish()

        self.assertEqual(story.status, 'published')
        self.assertTrue(republish_time <= story.published_at <= timezone.now())
        self.assertEqual(story.expires_at, story.published_at + timedelta(hours=24))
        self.assertTrue(story.is_active)
        self.assertFalse(story.is_expired)

    def test_edit_active_story_does_not_extend_lifetime(self):
        """Saving/editing an active story must NOT silently extend its 24-hour expiration lifetime."""
        original_published = timezone.now() - timedelta(hours=10)
        original_expires = original_published + timedelta(hours=24)

        story = Story.objects.create(
            title="Original Title",
            category="general",
            status="published",
            published_at=original_published,
            expires_at=original_expires,
            image=self.image,
            created_by=self.user
        )

        # Update title and description only
        story.title = "Updated Title"
        story.description = "Updated Description"
        story.save()

        story.refresh_from_db()
        self.assertEqual(story.title, "Updated Title")
        self.assertEqual(story.published_at, original_published)
        self.assertEqual(story.expires_at, original_expires)


class StoryApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='admin_api', password='password123', is_staff=True)
        self.image = create_test_image("poster_api.jpg")
        now = timezone.now()

        # Active story
        self.active_story = Story.objects.create(
            title="Public Exhibition",
            category="event",
            status="published",
            published_at=now - timedelta(hours=2),
            expires_at=now + timedelta(hours=22),
            image=self.image,
            created_by=self.user
        )

        # Expired story
        self.expired_story = Story.objects.create(
            title="Old Festival",
            category="festival",
            status="published",
            published_at=now - timedelta(hours=28),
            expires_at=now - timedelta(hours=4),
            image=self.image,
            created_by=self.user
        )

        # Draft story
        self.draft_story = Story.objects.create(
            title="Secret Draft",
            category="announcement",
            status="draft",
            image=self.image,
            created_by=self.user
        )

    def test_api_active_stories_returns_only_active(self):
        """Public /api/stories/ must return only currently active stories."""
        response = self.client.get(reverse('api_active_stories'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('stories', data)
        self.assertEqual(data['count'], 1)

        story_ids = [s['id'] for s in data['stories']]
        self.assertIn(self.active_story.id, story_ids)
        self.assertNotIn(self.expired_story.id, story_ids)
        self.assertNotIn(self.draft_story.id, story_ids)

        active_json = data['stories'][0]
        self.assertEqual(active_json['title'], "Public Exhibition")
        self.assertEqual(active_json['category'], "Event")
        self.assertTrue("poster_api" in active_json['image_url'])
        self.assertTrue(active_json['time_remaining_seconds'] > 0)

    def test_api_story_detail_active(self):
        """Active story detail returns 200 and story details."""
        response = self.client.get(reverse('api_story_detail', args=[self.active_story.id]))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['story']['id'], self.active_story.id)
        self.assertEqual(data['story']['title'], "Public Exhibition")

    def test_api_story_detail_expired_returns_404(self):
        """Accessing expired story via individual public endpoint must return 404."""
        response = self.client.get(reverse('api_story_detail', args=[self.expired_story.id]))
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn('error', data)

    def test_api_story_detail_draft_returns_404(self):
        """Accessing draft story via individual public endpoint must return 404."""
        response = self.client.get(reverse('api_story_detail', args=[self.draft_story.id]))
        self.assertEqual(response.status_code, 404)


class StoryAdminViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_user(username='admin_staff', password='password123', is_staff=True)
        self.image = create_test_image("admin_poster.jpg")

    def test_unauthorized_user_redirected_to_login(self):
        """Unauthenticated requests to admin story management views must redirect to admin login."""
        story = Story.objects.create(
            title="Sample Story",
            category="general",
            status="published",
            image=self.image,
            created_by=self.admin_user
        )

        urls = [
            reverse('manage_stories'),
            reverse('add_story'),
            reverse('update_story', args=[story.id]),
            reverse('publish_story', args=[story.id]),
            reverse('unpublish_story', args=[story.id]),
            reverse('delete_story', args=[story.id]),
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.url.startswith('/admin-login/'))

    def test_admin_can_create_and_publish_story(self):
        """An authorized admin can create and immediately publish a 24h story."""
        self.client.login(username='admin_staff', password='password123')
        test_img = create_test_image("new_announcement.png", ext="PNG")

        post_data = {
            'title': 'New Showroom Opening',
            'category': 'announcement',
            'description': 'Join us this Saturday for the launch.',
            'status': 'published',
            'image': test_img
        }

        response = self.client.post(reverse('add_story'), post_data, follow=True)
        self.assertEqual(response.status_code, 200)

        story = Story.objects.filter(title='New Showroom Opening').first()
        self.assertIsNotNone(story)
        self.assertEqual(story.status, 'published')
        self.assertTrue(story.is_active)
        self.assertEqual(story.expires_at, story.published_at + timedelta(hours=24))

    def test_admin_can_unpublish_and_republish(self):
        """Admin can unpublish an active story, and republishing resets its 24h cycle."""
        self.client.login(username='admin_staff', password='password123')
        story = Story.objects.create(
            title="Temporary Festival Poster",
            category="festival",
            status="published",
            image=self.image,
            created_by=self.admin_user
        )

        # Unpublish
        self.client.get(reverse('unpublish_story', args=[story.id]), follow=True)
        story.refresh_from_db()
        self.assertEqual(story.status, 'draft')
        self.assertFalse(story.is_active)

        # Republish
        now_before = timezone.now()
        self.client.get(reverse('publish_story', args=[story.id]), follow=True)
        story.refresh_from_db()
        self.assertEqual(story.status, 'published')
        self.assertTrue(story.is_active)
        self.assertTrue(story.published_at >= now_before)
        self.assertEqual(story.expires_at, story.published_at + timedelta(hours=24))

    def test_admin_can_edit_without_extending_lifetime(self):
        """Editing an active story via admin update view preserves the expiration timestamp."""
        self.client.login(username='admin_staff', password='password123')
        original_pub = timezone.now() - timedelta(hours=8)
        original_exp = original_pub + timedelta(hours=24)

        story = Story.objects.create(
            title="Initial Title",
            category="general",
            status="published",
            published_at=original_pub,
            expires_at=original_exp,
            image=self.image,
            created_by=self.admin_user
        )

        update_data = {
            'action': 'save',
            'title': 'Modified Title',
            'category': 'festival',
            'description': 'Updated description',
            'status': 'published',
        }
        response = self.client.post(reverse('update_story', args=[story.id]), update_data, follow=True)
        self.assertEqual(response.status_code, 200)

        story.refresh_from_db()
        self.assertEqual(story.title, 'Modified Title')
        self.assertEqual(story.category, 'festival')
        self.assertEqual(story.published_at, original_pub)
        self.assertEqual(story.expires_at, original_exp)

    def test_invalid_file_upload_rejected(self):
        """Submitting non-image or fake file is rejected safely."""
        self.client.login(username='admin_staff', password='password123')
        fake_file = SimpleUploadedFile("malicious.exe", b"binarycontent", content_type="application/octet-stream")

        post_data = {
            'title': 'Invalid File Story',
            'category': 'general',
            'status': 'published',
            'image': fake_file
        }
        response = self.client.post(reverse('add_story'), post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Story.objects.filter(title='Invalid File Story').exists())

    def test_admin_can_delete_story(self):
        """Deleting a story removes the DB record."""
        self.client.login(username='admin_staff', password='password123')
        story = Story.objects.create(
            title="To Delete",
            category="general",
            status="draft",
            image=self.image,
            created_by=self.admin_user
        )
        self.client.get(reverse('delete_story', args=[story.id]), follow=True)
        self.assertFalse(Story.objects.filter(id=story.id).exists())


class FrontendIntegrationAndRegressionTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='admin_web', password='password123', is_staff=True)
        self.image = create_test_image("web_poster.webp", ext="WEBP")

    def test_homepage_renders_with_stories_when_active(self):
        """Home page renders active story thumbnails when active stories exist."""
        story = Story.objects.create(
            title="Diwali Special",
            category="festival",
            status="published",
            image=self.image,
            created_by=self.user
        )
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Diwali Special")
        self.assertContains(response, "storiesContainer")
        self.assertContains(response, "storyViewerModal")

    def test_homepage_hides_stories_bar_when_no_active_stories(self):
        """Home page hides stories container with zero blank space when no active stories exist."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        # Check that hidden class is present on storiesContainer
        self.assertContains(response, 'id="storiesContainer"\n     class="stories-wrapper hidden')

    def test_existing_pages_regression(self):
        """Verify existing pages load without errors."""
        urls = [
            reverse('home'),
            reverse('about'),
            reverse('services'),
            reverse('gallery'),
            reverse('contact'),
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

    def test_admin_dashboard_shows_stories_entry(self):
        """Admin dashboard displays Manage Stories link and card for authenticated admin."""
        self.client.login(username='admin_web', password='password123')
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Manage Stories")
        self.assertContains(response, "Stories Management")
