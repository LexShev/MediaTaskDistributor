from django.urls import path

from . import views

urlpatterns = [
    path('review/', views.review_page, name='film_index_review'),
    path('api/queue/', views.api_queue, name='film_index_api_queue'),
    path('api/item/<int:program_id>/', views.api_item, name='film_index_api_item'),
    path('api/search/', views.api_search, name='film_index_api_search'),
    path('api/decide/', views.api_decide, name='film_index_api_decide'),
    path('api/lock/<int:program_id>/', views.api_lock, name='film_index_api_lock'),
    path('api/unlock/<int:program_id>/', views.api_unlock, name='film_index_api_unlock'),
]
