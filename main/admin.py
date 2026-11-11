from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Announcement, Gallery, Giving, MeetingReport, Welfare, Publication, Event, PublicationPayment
from ticketing.admin import SpeakerInline, TicketTypeInline

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
    list_display = ('title', 'event_date', 'city', 'is_featured', 'ticketing_enabled')
    list_filter = ('is_featured', 'ticketing_enabled', 'event_date')
    search_fields = ('title', 'theme', 'city')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [TicketTypeInline, SpeakerInline]
