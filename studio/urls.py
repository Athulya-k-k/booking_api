from django.urls import path
from . import views



urlpatterns = [
    # Authentication
    path('', views.home_view, name='home'),
    path('', views.login_view, name='login'),  # Root
    path('login/', views.login_view, name='login'),  
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),

    # User actions
    path('book/<int:class_id>/', views.book_class_page, name='book_class_page'),
    path('cancel-booking/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),

    # Admin actions
    path('class/create/', views.create_class, name='create_class'),
    path('class/edit/<int:class_id>/', views.edit_class, name='edit_class'),
    path('class/delete/<int:class_id>/', views.delete_class, name='delete_class'),

    # Dashboards
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/user/', views.user_dashboard, name='user_dashboard'),
]
