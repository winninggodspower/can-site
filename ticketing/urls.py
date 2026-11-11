from django.urls import path
from . import views

app_name = 'ticketing'

urlpatterns = [
    path('<slug:slug>/', views.event_detail_view, name='event_detail'),
    path('<slug:slug>/checkout/', views.initiate_ticket_checkout, name='initiate_checkout'),
    path('<slug:slug>/check-in/', views.staff_checkin_view, name='staff_checkin'),
    path('tickets/verify/', views.payment_verify_view, name='payment_verify'),
    path('order/<str:reference>/', views.order_confirmation_view, name='order_confirmation'),
    path('order/<str:reference>/pdf/', views.ticket_pdf_view, name='ticket_pdf'),
]

