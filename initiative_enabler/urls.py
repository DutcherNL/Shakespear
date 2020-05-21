from django.urls import path, include

from initiative_enabler import views

app_name = "collectives"

urlpatterns = [
    path('', views.CollectiveOverview.as_view(), name='overview'),
    path('action/', views.TakeActionOverview.as_view(), name='take_action'),
    path('g/', include([
        path('', views.InitiatedCollectiveOverview.as_view(), name='active_overview'),
        path('<int:collective_id>/', include([
            path('start_new/', views.StartCollectiveView.as_view(), name='start_new'),
            path('details/', views.CollectiveInfoView.as_view(), name='general_info')
        ])),
    ])),
    path('u/', include([
        path('rsvp/<slug:rsvp_slug>/', include([
            path('', views.CollectiveRSVPView.as_view(), name='rsvp'),
            path('denied/', views.CollectiveRSVPDeniedView.as_view(), name='rsvp_deny'),
        ])),
        path('<int:collective_id>/', include([
            path('details/', views.render_collective_detail, name='actief_collectief_details'),
            path('edit-contact-info/', views.AdjustPersonalData.as_view(), name='edit_contact_data'),
            path('invite/', views.SendNewInvitesView.as_view(), name='active_collective_invite_new'),
            path('open/', views.ChangeCollectiveStateView.as_view(), name='active_collective_change_open_state'),
            path('send_reminder/', views.SendReminderRSVPsView.as_view(), name='send_reminders_view'),
        ])),
    ])),
]
