from django.conf.urls import url
from SilentD import views
from django.views.generic import TemplateView

urlpatterns = [
    url(r'^register/$', views.register, name='register'),
    url(r'^logout/$', views.user_logout, name='logout'),
    url(r'^file_upload/$', views.file_upload, name='file_upload'),
    url(r'^index',  TemplateView.as_view(template_name='SilentD/index.html'), name='index'),
    url(r'^genesippr/$', views.genesippr, name='genesippr'),
    url(r'^createproject/$', views.create_project, name='create_project'),
    url(r'^projects/$', views.projects, name='projects')
    ]
