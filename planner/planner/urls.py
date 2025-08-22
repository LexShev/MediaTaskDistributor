"""
URL configuration for planner project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import handler400, handler403, handler404, handler500

handler400 = 'main.views.bad_request'
handler403 = 'main.views.permission_denied'
handler404 = 'main.views.page_not_found'
handler500 = 'main.views.server_error'

urlpatterns = ([
    path("admin/", admin.site.urls),
    path("", include('home.urls')),
    path("", include('main.urls')),
    path("otk/", include('otk.urls')),
    path("on-air-report/", include('on_air_report.urls')),
    path("", include('common_pool.urls')),
    path("messenger/", include('messenger_static.urls')),
    path("", include('advanced_search.urls')),
    path("task_manager/", include('admin_work_panel.urls')),
    path("", include('distribution.urls')),
    path("desktop/", include('desktop.urls')),
    path("tools/", include('tools.urls')),
    path("authorize/", include('django.contrib.auth.urls')),
    path("authorize/", include('workers.urls'))
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
               + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT))
