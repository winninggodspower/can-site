from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Announcement, Gallery, Giving, MeetingReport, Welfare, Publication, Event, PublicationPayment

@admin.register(Announcement)
class AnnouncementAdmin(ModelAdmin):
    pass

@admin.register(Gallery)
class GalleryAdmin(ModelAdmin):
    pass

@admin.register(Giving)
class GivingAdmin(ModelAdmin):
    pass

@admin.register(MeetingReport)
class MeetingReportAdmin(ModelAdmin):
    pass

@admin.register(Welfare)
class WelfareAdmin(ModelAdmin):
    pass

@admin.register(Publication)
class PublicationAdmin(ModelAdmin):
    pass

@admin.register(PublicationPayment)
class PublicationPaymentAdmin(ModelAdmin):
    pass

@admin.register(Event)
class EventAdmin(ModelAdmin):
    pass