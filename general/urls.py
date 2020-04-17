from django.urls import path, include
from general import views

from general.site import page_site

app_name = 'general'

urlpatterns = [
    path('accounts/', include([
        path('login/', views.LogInView.as_view(), name='login'),
        path('logout/', views.LogOutView.as_view(), name='logout'),

    ])),
    path('<slug:slug>/', page_site.urls),
]
