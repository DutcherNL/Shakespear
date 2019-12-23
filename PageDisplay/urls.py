from django.urls import path, include

from . import views

app_name = "pages"

urlpatterns = [
    path('', views.PageOverview.as_view(), name='overview'),
    path('<int:page_id>/', include([
        path('', views.PageInfoView.as_view(), name='info_page'),
        # Editing can not be done without a page site
        # It an be displayed though
        ]))
]


