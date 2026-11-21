from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from datetime import timedelta
import os
from PIL import Image as PILImage

from .models import *

def home(request):
    """Render the main home page with active stories."""
    active_stories = Story.get_active_stories()
    return render(request, 'home.html', {'active_stories': active_stories})


def aboutus(request):
    """Render the about us page."""
    return render(request, 'aboutus.html')


def services(request):
    """Render the services page."""
    return render(request, 'services.html')


def contact(request):
    """Handle contact form submissions and render the contact page."""
    try:
        if request.method == 'POST':
            name = request.POST.get('name')
            email = request.POST.get('email')
            mobile = request.POST.get('mobile')
            message = request.POST.get('message')

            inquiry = Inquiry.objects.create(
                name=name,
                email=email,
                mobile=mobile,
                message=message
            )
            messages.success(request, "Inquiry added successfully!")
            return redirect('contact')
    except Exception:
        messages.error(request, "Something went wrong!")
    return render(request, 'contact.html')


def gallery(request):
    """Render the main gallery page displaying all categories."""
    try:
        categories = Category.objects.all()
    except Exception:
        messages.error(request, "Something went wrong!")
    return render(request, 'gallery.html', {'categories': categories})


def sub_gallery(request, title):
    """Render a specific gallery category and its associated images."""
    try:
        category = get_object_or_404(Category, title=title)
        images = Image.objects.filter(category=category)
    except Exception:
        messages.error(request, "Something went wrong!")
    return render(request, 'category_gallery.html', {'images': images, 'category': category})


def admin_login(request):
    """Handle admin authentication and login."""
    try:
        if request.user.is_authenticated:
            return redirect('admin_dashboard')
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user=user)
                messages.success(request, "Logged in successfully!")
                return redirect('admin_dashboard')
            else:
                messages.error(request, "Invalid username or password!")

    except Exception:
        messages.error(request, "Something went wrong!")

    return render(request, 'admin/admin_login.html')


@login_required(login_url='admin_login')
def logout_view(request):
    """Log out the current user and redirect to login."""
    logout(request)
    messages.success(request, "Logged out successfully!")
    return redirect('admin_login')


@login_required(login_url='admin_login')
def admin_dashboard(request):
    """Render the main admin dashboard."""
    return render(request, 'admin/admin_dashboard.html')


@login_required(login_url='admin_login')
def add_admin(request):
    """Handle creation of new admin users."""
    try:
        admins = User.objects.filter(is_superuser=False)
        roles = Profile.ROLE_CHOICES
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')
            role = request.POST.get('role')

            if User.objects.filter(username=username).exists():
                messages.error(request, "Username already exists!")
            else:
                user = User.objects.create_user(
                    username=username, password=password, is_staff=True, is_superuser=False)

                profile = user.profile
                profile.role = role
                profile.save()

                messages.success(request, "Admin added successfully!")
                return redirect('add_admin')

    except Exception:
        messages.error(request, "Something went wrong!")

    return render(request, 'admin/add_admin.html', {'roles': roles, 'admins': admins})


@login_required(login_url='admin_login')
def update_admin(request, pk):
    """Update an existing admin user's details and role."""
    try:
        roles = Profile.ROLE_CHOICES
        admin = get_object_or_404(User, pk=pk)
        if admin.is_superuser:
            messages.error(request, "Super Admin cannot be updated!")
            return redirect('admin_dashboard')
        if request.user.profile.role == 'admin':
            messages.error(
                request, "You are not authorized to update this admin!")
            return redirect('admin_dashboard')
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')
            role = request.POST.get('role')
            admin.username = username
            if role:
                admin.profile.role = role
            if password:
                admin.set_password(password)
            admin.save()
            messages.success(request, "Admin updated successfully!")
            return redirect('admin_dashboard')

    except Exception:
        messages.error(request, "Something went wrong!")

    return render(request, 'admin/update_admin.html', {'admin': admin, 'roles': roles})


@login_required(login_url='admin_login')
def delete_admin(request, pk):
    """Delete an admin user. Ensure super admins cannot be deleted."""
    try:
        admin = get_object_or_404(User, pk=pk)
        if admin.is_superuser:
            messages.error(request, "Super Admin cannot be Deleted!")
            return redirect('add_admin')
        if request.user.profile.role == 'admin':
            messages.error(
                request, "You are not authorized to delete this admin!")
            return redirect('add_admin')
        if request.user == admin:
            messages.error(request, "You cannot delete yourself!")
            return redirect('add_admin')
        admin.delete()
        messages.success(request, "Admin deleted successfully!")
        return redirect('add_admin')
    except Exception:
        messages.error(request, "Something went wrong!")
    return render(request, 'admin/add_admin.html')


@login_required(login_url='admin_login')
def add_category(request):
    """Create a new image category/album for the gallery."""
    try:
        categories = Category.objects.all()
        if request.method == 'POST':
            image = request.FILES.get('image')
            title = request.POST.get('title')
            description = request.POST.get('description')

            if Category.objects.filter(title=title).exists():
                messages.error(request, "Category already exists!")
            else:
                category = Category.objects.create(
                    image=image,
                    title=title,
                    description=description
                )
                messages.success(request, "Category added successfully!")
                return redirect('add_category')

    except Exception:
        messages.error(request, "Something went wrong!")

    return render(request, 'admin/add_category.html', {'categories': categories})


@login_required(login_url='admin_login')
def update_category(request, pk):
    """Update an existing category's details."""
    try:
        category = get_object_or_404(Category, pk=pk)
        if request.method == 'POST':
            image = request.FILES.get('image')
            title = request.POST.get('title')
            description = request.POST.get('description')
            if image:
                category.image = image
            if title:
                category.title = title
            if description:
                category.description = description
            category.save()
            messages.success(request, "Category updated successfully!")
            return redirect('add_category')
    except Exception:
        messages.error(request, "Something went wrong!")
    return render(request, 'admin/update_category.html', {'category': category})


@login_required(login_url='admin_login')
def delete_category(request, pk):
    """Delete a category and securely remove its associated image files."""
    try:
        category = get_object_or_404(Category, pk=pk)

        # get all images of this category
        images = Image.objects.filter(category=category)

        if category.image:
            category.image.delete(save=False)

        # delete each image file + record
        for img in images:
            if img.image:
                img.image.delete(save=False)
            img.delete()

        # now delete category
        category.delete()

        messages.success(
            request, "Category and its images deleted successfully!")
        return redirect('add_category')

    except Exception:
        messages.error(request, "Something went wrong!")

    return render(request, 'admin/add_category.html')



@login_required(login_url='admin_login')
def add_image(request):
    """Upload new images to a category."""
    try:
        images = Image.objects.all()
        categories = Category.objects.values('id', 'title')
        if request.method == 'POST':
            if 'upload_image' in request.POST:
                category_id = request.POST.get('category')
                image_files = request.FILES.getlist('image')
                category = Category.objects.get(id=category_id)
                for img in image_files:   # ✅ loop each image
                    Image.objects.create(
                        category=category,
                        image=img
                    )
                messages.success(request, "Image added successfully!")
                return redirect('add_image')
    except Exception as e:
        messages.error(request, "Something went wrong!")
        print(e)
    return render(request, 'admin/add_image.html', {'categories': categories, 'images': images})


@login_required(login_url='admin_login')
def update_image(request, pk):
    """Update an existing image's details."""
    try:
        image_obj = get_object_or_404(Image, pk=pk)
        categories = Category.objects.values('id', 'title')
        if request.method == 'POST':
            image = request.FILES.get('image')
            category_id = request.POST.get('category')
            if category_id:
                category = Category.objects.get(id=category_id)
                image_obj.category = category
            if image:
                image_obj.image = image
            image_obj.save()
            messages.success(request, "Image updated successfully!")
            return redirect('add_image')
    except Exception as e:
        messages.error(request, "Something went wrong!")
        print(e)
    return render(request, 'admin/update_image.html', {'image': image, 'categories': categories})


@login_required(login_url='admin_login')
def delete_image(request, pk):
    """Delete a specific image and its file."""
    try:
        image = get_object_or_404(Image, pk=pk)
        if image.image:  # delete file from MEDIA
            image.image.delete(save=False)
        image.delete()  # delete DB record
        messages.success(request, "Image deleted successfully!")
        return redirect('add_image')
    
    except Exception:
        messages.error(request, "Something went wrong!")

    return render(request, 'admin/add_image.html')



@login_required(login_url='admin_login')
def delete_all_images(request):
    """Delete all images and their associated files in the system."""
    if request.method == "POST":
        if 'delete_all_images' in request.POST:
            images = Image.objects.all()

            for img in images:
                if img.image:  # check if file exists
                    img.image.delete(save=False)  # delete file from storage
                img.delete()  # delete DB record

            messages.success(request, "All images and files deleted successfully.")

    return redirect('add_image')

@login_required(login_url='admin_login')
def inquiry(request):
    """List all submitted contact inquiries."""
    try:
        inquiries = Inquiry.objects.all()
    except Exception:
        messages.error(request, "Something went wrong!")
    return render(request, 'admin/list_inquiry.html', {'inquiries': inquiries})


@login_required(login_url='admin_login')
def delete_inquiry(request, pk):
    """Delete a specific inquiry."""
    try:

        inquiry = get_object_or_404(Inquiry, pk=pk)
        inquiry.delete()
        messages.success(request, "Inquiry deleted successfully!")
        return redirect('admin_dashboard')

    except Exception:
        messages.error(request, "Something went wrong!")

    return render(request, 'admin/admin_dashboard.html')


# ==========================================
# STORY VALIDATION & HELPER FUNCTIONS
# ==========================================

ALLOWED_STORY_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
MAX_STORY_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB


def validate_story_image(file):
    """
    Validates uploaded story image file extension, size, and image integrity.
    Supports JPG, JPEG, PNG, and WebP up to 10MB.
    Returns (True, None) if valid, or (False, error_message).
    """
    if not file:
        return False, "Poster/Image file is required."
    
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ALLOWED_STORY_EXTENSIONS:
        return False, f"Unsupported file type '{ext}'. Allowed types: JPG, JPEG, PNG, WebP."

    if file.size > MAX_STORY_UPLOAD_SIZE:
        return False, f"File size exceeds maximum allowed limit of 10MB."

    try:
        img = PILImage.open(file)
        img.verify()
        if hasattr(file, 'seek'):
            file.seek(0)
    except Exception:
        return False, "Uploaded file is not a valid or readable image."

    return True, None


# ==========================================
# PUBLIC STORY APIS
# ==========================================

def api_active_stories(request):
    """
    Public API returning active stories that have been published and not yet expired.
    Expired and draft stories are strictly excluded from results.
    """
    stories = Story.get_active_stories()
    data = []
    for s in stories:
        data.append({
            'id': s.id,
            'title': s.title,
            'description': s.description,
            'category': s.get_category_display(),
            'category_code': s.category,
            'image_url': s.image.url if s.image else '',
            'published_at': s.published_at.isoformat() if s.published_at else '',
            'expires_at': s.expires_at.isoformat() if s.expires_at else '',
            'time_remaining_seconds': s.time_remaining_seconds,
            'time_remaining_display': s.time_remaining_display,
        })
    return JsonResponse({'stories': data, 'count': len(data)})


def api_story_detail(request, pk):
    """
    Public API returning details of a single active story.
    Returns 404 if the story does not exist, is draft, or has expired.
    """
    story = Story.get_active_stories().filter(pk=pk).first()
    if not story:
        return JsonResponse({'error': 'Story not found or has expired.'}, status=404)
    return JsonResponse({
        'story': {
            'id': story.id,
            'title': story.title,
            'description': story.description,
            'category': story.get_category_display(),
            'category_code': story.category,
            'image_url': story.image.url if story.image else '',
            'published_at': story.published_at.isoformat() if story.published_at else '',
            'expires_at': story.expires_at.isoformat() if story.expires_at else '',
            'time_remaining_seconds': story.time_remaining_seconds,
            'time_remaining_display': story.time_remaining_display,
        }
    })


# ==========================================
# ADMIN STORY MANAGEMENT VIEWS
# ==========================================

@login_required(login_url='admin_login')
def manage_stories(request):
    """
    Admin stories management dashboard.
    Lists all stories with filtering and provides story creation interface.
    """
    status_filter = request.GET.get('status', 'all')
    all_stories = list(Story.objects.all().order_by('-created_at'))

    # Calculate status counts for filter badges
    counts = {
        'all': len(all_stories),
        'active': 0,
        'draft': 0,
        'scheduled': 0,
        'expired': 0,
    }
    for s in all_stories:
        st = s.computed_status
        if st in counts:
            counts[st] += 1

    # Filter stories based on query parameter
    if status_filter == 'active':
        filtered_stories = [s for s in all_stories if s.computed_status == 'active']
    elif status_filter == 'draft':
        filtered_stories = [s for s in all_stories if s.computed_status == 'draft']
    elif status_filter == 'scheduled':
        filtered_stories = [s for s in all_stories if s.computed_status == 'scheduled']
    elif status_filter == 'expired':
        filtered_stories = [s for s in all_stories if s.computed_status == 'expired']
    else:
        filtered_stories = all_stories

    categories = Story.CATEGORY_CHOICES
    statuses = Story.STATUS_CHOICES

    return render(request, 'admin/manage_stories.html', {
        'stories': filtered_stories,
        'counts': counts,
        'status_filter': status_filter,
        'categories': categories,
        'statuses': statuses,
    })


@login_required(login_url='admin_login')
def add_story(request):
    """
    Handle creation of new stories by administrators.
    Supports draft, published (24-hour expiration), and scheduled stories.
    """
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        category = request.POST.get('category', 'general')
        status = request.POST.get('status', 'draft')
        scheduled_at_str = request.POST.get('scheduled_at', '').strip()
        image_file = request.FILES.get('image')

        if not title:
            messages.error(request, "Story title is required.")
            return redirect('manage_stories')

        valid, err = validate_story_image(image_file)
        if not valid:
            messages.error(request, err)
            return redirect('manage_stories')

        scheduled_at = None
        if status == 'scheduled':
            if not scheduled_at_str:
                messages.error(request, "Scheduled date and time are required for scheduled stories.")
                return redirect('manage_stories')
            try:
                parsed_dt = parse_datetime(scheduled_at_str)
                if parsed_dt and timezone.is_naive(parsed_dt):
                    scheduled_at = timezone.make_aware(parsed_dt)
                else:
                    scheduled_at = parsed_dt
            except Exception:
                messages.error(request, "Invalid scheduled date/time format.")
                return redirect('manage_stories')

        story = Story(
            title=title,
            description=description,
            category=category,
            status=status,
            image=image_file,
            scheduled_at=scheduled_at,
            created_by=request.user
        )

        now = timezone.now()
        if status == 'published':
            story.published_at = now
            story.expires_at = now + timedelta(hours=24)
        elif status == 'scheduled' and scheduled_at:
            story.published_at = scheduled_at
            story.expires_at = scheduled_at + timedelta(hours=24)

        story.save()

        if status == 'published':
            messages.success(request, f"Story '{title}' published successfully! It will automatically expire in 24 hours.")
        elif status == 'scheduled':
            messages.success(request, f"Story '{title}' scheduled successfully for {scheduled_at.strftime('%b %d, %Y %H:%M')}.")
        else:
            messages.success(request, f"Story '{title}' saved as draft.")

        return redirect('manage_stories')

    return redirect('manage_stories')


@login_required(login_url='admin_login')
def update_story(request, pk):
    """
    Edit an existing story.
    Editing an active story preserves its existing publication and expiration timestamps.
    Republishing resets the 24-hour cycle from the current timestamp.
    """
    story = get_object_or_404(Story, pk=pk)

    if request.method == 'POST':
        action = request.POST.get('action', 'save')
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        category = request.POST.get('category', story.category)
        status = request.POST.get('status', story.status)
        scheduled_at_str = request.POST.get('scheduled_at', '').strip()
        new_image = request.FILES.get('image')

        if not title:
            messages.error(request, "Story title cannot be empty.")
            return render(request, 'admin/update_story.html', {'story': story, 'categories': Story.CATEGORY_CHOICES, 'statuses': Story.STATUS_CHOICES})

        if new_image:
            valid, err = validate_story_image(new_image)
            if not valid:
                messages.error(request, err)
                return render(request, 'admin/update_story.html', {'story': story, 'categories': Story.CATEGORY_CHOICES, 'statuses': Story.STATUS_CHOICES})
            if story.image:
                story.image.delete(save=False)
            story.image = new_image

        story.title = title
        story.description = description
        story.category = category

        scheduled_at = None
        if scheduled_at_str:
            try:
                parsed_dt = parse_datetime(scheduled_at_str)
                if parsed_dt and timezone.is_naive(parsed_dt):
                    scheduled_at = timezone.make_aware(parsed_dt)
                else:
                    scheduled_at = parsed_dt
            except Exception:
                messages.error(request, "Invalid scheduled date/time format.")
                return render(request, 'admin/update_story.html', {'story': story, 'categories': Story.CATEGORY_CHOICES, 'statuses': Story.STATUS_CHOICES})

        now = timezone.now()

        if action == 'republish':
            # Explicit republish: reset 24h clock from right now
            story.publish(save=False)
            messages.success(request, f"Story '{story.title}' republished successfully! Expiration timer reset for 24 hours.")
        elif action == 'unpublish':
            story.unpublish(save=False)
            messages.success(request, f"Story '{story.title}' unpublished.")
        else:
            # Regular save / update
            previous_status = story.status
            story.status = status

            if status == 'published':
                if previous_status != 'published' or story.is_expired:
                    # Transitioning from draft/expired to published -> start fresh 24h cycle
                    story.published_at = now
                    story.expires_at = now + timedelta(hours=24)
                # If already active and published, keep published_at and expires_at unchanged!
            elif status == 'scheduled':
                if scheduled_at:
                    story.scheduled_at = scheduled_at
                    story.published_at = scheduled_at
                    story.expires_at = scheduled_at + timedelta(hours=24)
            elif status == 'draft':
                # Saved as draft; removed from public display
                pass

            messages.success(request, f"Story '{story.title}' updated successfully.")

        story.save()
        return redirect('manage_stories')

    return render(request, 'admin/update_story.html', {
        'story': story,
        'categories': Story.CATEGORY_CHOICES,
        'statuses': Story.STATUS_CHOICES,
    })


@login_required(login_url='admin_login')
def publish_story(request, pk):
    """
    Quick action to publish or republish a story, resetting its 24-hour expiration window.
    """
    story = get_object_or_404(Story, pk=pk)
    story.publish()
    messages.success(request, f"Story '{story.title}' published successfully! It will remain active for 24 hours.")
    return redirect('manage_stories')


@login_required(login_url='admin_login')
def unpublish_story(request, pk):
    """
    Quick action to unpublish a story immediately.
    """
    story = get_object_or_404(Story, pk=pk)
    story.unpublish()
    messages.success(request, f"Story '{story.title}' unpublished immediately.")
    return redirect('manage_stories')


@login_required(login_url='admin_login')
def delete_story(request, pk):
    """
    Delete a story and its associated poster image file.
    """
    story = get_object_or_404(Story, pk=pk)
    title = story.title
    story.delete()
    messages.success(request, f"Story '{title}' deleted successfully.")
    return redirect('manage_stories')
