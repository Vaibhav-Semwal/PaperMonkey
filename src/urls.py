from django.urls import path,  include
from .views import Index, SignUpView, LogInView, Dashboard, PaperCreateView, EditPaperView
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', Index.as_view(), name='index'),

    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', LogInView.as_view(template_name='auth/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='auth/logout.html'), name='logout'),
    
    path('dashboard/', Dashboard.as_view(), name='dashboard'),
    
    path('additem/', PaperCreateView.as_view(), name='additem'),
    path("<uuid:pk>/edit/", EditPaperView.as_view(), name="edit_paper"),
]
