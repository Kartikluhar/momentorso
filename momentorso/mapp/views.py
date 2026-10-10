from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User

from .models import *

def home(request):
    """Render the main home page."""
    return render(request, 'home.html')


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
