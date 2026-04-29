from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='index'),

    path('processing/<int:image_id>/', views.processing),
    path('visualize/<int:image_id>/', views.visualizer_page, name='visualizer'),
    path('compare/<int:image_id>/', views.comparison_page, name='comparison'),
    
    # PDF route must come BEFORE the general report route
    path('report/pdf/<int:image_id>/', views.generate_report_pdf),
    path('report/<int:image_id>/', views.report_page, name='report'),

    path('sort/<int:image_id>/', views.sort_visual),

    path('login/', views.login_view, name = 'login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),

    path('support/', views.support_page, name='support'),
    path('faq/', views.faq_page, name='faq'),

    path('array/', views.array_visualizer, name='array_visualizer'),
    path('api/sort_array/', views.sort_array_api, name='sort_array_api'),
]