from django.urls import path, include

from initiative_enabler import views

app_name = "collectives"

urlpatterns = [
    path('', views.CollectiveOverview.as_view(), name='overview'),
    path('g/', include([
        path('', views.InitiatedCollectiveOverview.as_view(), name='active_overview'),
        path('<int:collective_id>/', include([
            path('start_new/', views.StartCollectiveView.as_view(), name='start_new'),
        ])),
    ])),
    path('u/', include([
        path('rsvp/<slug:rsvp_slug>/', include([
            path('', views.CollectiveRSVPView.as_view(), name='rsvp'),
            path('denied/', views.CollectiveRSVPDeniedView.as_view(), name='rsvp_deny'),
        ])),
        path('<int:collective_id>/', include([
            path('details/', views.InitiatedCollectiveDetailsView.as_view(), name='actief_collectief_details'),
            path('close/', views.CloseCollectiveView.as_view(), name='active_collective_close_entry'),
            path('open/', views.OpenCollectiveView.as_view(), name='active_collective_open_entry'),
        ])),
    ])),
]
