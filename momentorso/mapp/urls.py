from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.aboutus, name='about'),
    path('services/', views.services, name='services'),
    path('contact/', views.contact, name='contact'),
    path('gallery/', views.gallery, name='gallery'),

    # For Admin
    path('admin-login/', views.admin_login, name='admin_login'),
    path('logout/', views.logout_view, name='logout'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('add-admin/', views.add_admin, name='add_admin'),
    path('update-admin/<int:pk>/', views.update_admin, name='update_admin'),
    path('delete-admin/<int:pk>/', views.delete_admin, name='delete_admin'),

    # For Category
    path('add-category/', views.add_category, name='add_category'),
    path('update-category/<int:pk>/', views.update_category, name='update_category'),
    path('delete-category/<int:pk>/', views.delete_category, name='delete_category'),

    # For Images
    path('add-image/', views.add_image, name='add_image'),
    path('update-image/<int:pk>/', views.update_image, name='update_image'),
    path('delete-image/<int:pk>/', views.delete_image, name='delete_image'),
    path('delete-all-images/', views.delete_all_images, name='delete_all_images'),
    path('sub-gallery/<str:title>/', views.sub_gallery, name='sub_gallery'),

    # For Inquiries
    path('inquiry/', views.inquiry, name='inquiry'),
    path('delete-inquiry/<int:pk>/', views.delete_inquiry, name='delete_inquiry'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)