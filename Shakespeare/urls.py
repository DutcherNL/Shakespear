"""Shakespeare URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from .index import index

from Questionaire.techpages import tech_page_site
from PageDisplay.sites import page_site

urlpatterns = [
    path('', index, name='index'),
    path('admin/', admin.site.urls),
    path('Q/', include('Questionaire.urls')),
    path('setup/', include('Questionaire.setup.urls')),
    path('mails/', include('mailing.urls')),
    path('pages/', include('PageDisplay.urls')),
    path('techs/<slug:slug>/', tech_page_site.urls),
    path('test/', page_site.urls),
    path('collective/', include('initiative_enabler.urls')),
    path('mijndata/', include('inquirer_settings.urls')),
    path('data_analysis/', include('data_analysis.urls')),
    path('', include('general.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
