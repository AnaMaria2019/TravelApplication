from django.urls import path, include, re_path
from django.contrib.auth.views import LoginView, LogoutView

from .views import *

urlpatterns = [
    path('login', LoginView.as_view(template_name='app/login_form.html'), name='user_login'),
    path('logout', LogoutView.as_view(), name='user_logout'),
    path('signup', SignUpView.as_view(), name='user_signup'),
    path('about', about, name='app_about'),
    path('fav_destinations', choose_destinations, name='app_choose_fav_destinations'),
    path('post_fav_cities', fav_cities, name='app_post_fav_cities'),
    path('search_form', search_form, name='app_search_form'),
    path('show_flight', show_flight, name='app_show_flight'),
    path('get_flight', get_flight, name='app_get_flight'),
    path('search_accommodation', search_accommodation, name='app_search_accommodation'),
    path('show_accommodation', show_accommodation, name='app_show_accommodation'),
    path('get_accommodation', get_accommodation, name='app_get_accommodation'),
    re_path('poll_state', poll_state, name='poll_state'),
]
