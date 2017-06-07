from django.conf.urls import include, url
from django.contrib import admin
from SilentD import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', views.user_login, name='login'),
    url(r'^bio/', include('SilentD.urls')),
    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_PATH)
