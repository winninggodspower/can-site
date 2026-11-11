from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from .models import Speaker, TicketType, TicketOrder, Ticket


class SpeakerInline(TabularInline):
    model = Speaker
    extra = 1
    fields = ('name', 'title_or_role', 'photo', 'photo_static', 'order')


class TicketTypeInline(TabularInline):
    model = TicketType
    extra = 1
    fields = ('name', 'price', 'quantity', 'max_per_order', 'is_active')


class TicketInline(TabularInline):
    model = Ticket
    extra = 0
    readonly_fields = ('ticket_code', 'attendee_name', 'ticket_type', 'checked_in', 'checked_in_at')
    can_delete = False


@admin.register(Speaker)
class SpeakerAdmin(ModelAdmin):
    list_display = ('name', 'event', 'title_or_role', 'order')
    list_filter = ('event',)
    search_fields = ('name', 'title_or_role')


@admin.register(TicketType)
class TicketTypeAdmin(ModelAdmin):
    list_display = ('name', 'event', 'price', 'quantity', 'sold_count', 'remaining', 'is_active')
    list_filter = ('event', 'is_active')
    search_fields = ('name', 'event__title')


@admin.register(TicketOrder)
class TicketOrderAdmin(ModelAdmin):
    list_display = ('reference', 'full_name', 'email', 'phone', 'event', 'ticket_type', 'quantity', 'total_amount', 'status', 'created_at')
    list_filter = ('status', 'event', 'ticket_type')
    search_fields = ('reference', 'full_name', 'email', 'phone', 'paystack_reference')
    readonly_fields = ('reference', 'total_amount', 'created_at', 'paid_at', 'paystack_reference')
    inlines = [TicketInline]


@admin.register(Ticket)
class TicketAdmin(ModelAdmin):
    list_display = ('ticket_code', 'attendee_name', 'order', 'ticket_type', 'checked_in', 'checked_in_at')
    list_filter = ('checked_in', 'ticket_type__event')
    search_fields = ('ticket_code', 'attendee_name', 'order__reference', 'order__email')
    readonly_fields = ('ticket_code', 'order', 'ticket_type', 'attendee_name')

