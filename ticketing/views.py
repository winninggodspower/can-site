import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.http import HttpResponse

from main.models import Event
from .models import TicketType, TicketOrder, Ticket
from .services import (
    TicketServiceError,
    create_ticket_order,
    initiate_paystack_checkout,
    verify_and_fulfil_order,
    fulfil_ticket_order,
    generate_ticket_pdf,
    check_in_ticket,
)

logger = logging.getLogger(__name__)


def event_detail_view(request, slug):
    """Dedicated event page with flyer, details, speakers, and checkout form."""
    event = get_object_or_404(Event, slug=slug)
    ticket_types = event.ticket_types.filter(is_active=True)
    speakers = event.speakers.all()
    primary_ticket = ticket_types.first()

    context = {
        'event': event,
        'ticket_types': ticket_types,
        'primary_ticket': primary_ticket,
        'speakers': speakers,
    }
    return render(request, 'ticketing/event_detail.html', context)


def initiate_ticket_checkout(request, slug):
    """Handle ticket purchase and redirect to Paystack."""
    if request.method != 'POST':
        return redirect('ticketing:event_detail', slug=slug)

    event = get_object_or_404(Event, slug=slug, ticketing_enabled=True)
    ticket_type_id = request.POST.get('ticket_type')
    ticket_type = get_object_or_404(TicketType, id=ticket_type_id, event=event, is_active=True)

    try:
        order = create_ticket_order(
            event=event,
            ticket_type=ticket_type,
            quantity=request.POST.get('quantity', 1),
            full_name=request.POST.get('full_name', ''),
            email=request.POST.get('email', ''),
            phone=request.POST.get('phone', ''),
            user=request.user,
        )
    except TicketServiceError as e:
        messages.error(request, str(e))
        return redirect('ticketing:event_detail', slug=slug)

    # Free ticket bypass
    if order.total_amount == 0:
        fulfil_ticket_order(order)
        messages.success(request, "Your registration was successful!")
        return redirect('ticketing:order_confirmation', reference=order.reference)

    # Paystack checkout
    callback_url = request.build_absolute_uri(reverse('ticketing:payment_verify'))
    redirect_url = initiate_paystack_checkout(order, callback_url)

    if redirect_url:
        return redirect(redirect_url)
    else:
        messages.error(request, "Unable to connect to the payment gateway. Please try again shortly.")
        return redirect('ticketing:event_detail', slug=slug)


def payment_verify_view(request):
    """Callback after Paystack payment."""
    reference = request.GET.get('reference')
    if not reference:
        messages.error(request, "Missing transaction reference.")
        return redirect('/')

    success, order, error_message = verify_and_fulfil_order(reference)
    if not order:
        messages.error(request, error_message or "Order record not found.")
        return redirect('/')

    if success:
        messages.success(request, f"Payment successful! Your tickets for {order.event.title} are confirmed.")
        return redirect('ticketing:order_confirmation', reference=order.reference)
    else:
        messages.error(request, error_message or "Payment could not be verified.")
        return redirect('ticketing:event_detail', slug=order.event.slug)


def order_confirmation_view(request, reference):
    """Confirmation page displaying issued tickets and event passes."""
    order = get_object_or_404(TicketOrder, reference=reference)
    tickets = order.tickets.all()
    return render(request, 'ticketing/order_confirmation.html', {'order': order, 'tickets': tickets})


def ticket_pdf_view(request, reference):
    """Generate printable PDF tickets using the PDF service."""
    order = get_object_or_404(TicketOrder, reference=reference, status=TicketOrder.STATUS_PAID)
    buffer = generate_ticket_pdf(order)

    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="tickets-{order.reference}.pdf"'
    return response


def staff_checkin_view(request, slug):
    """Staff ticket scanner / check-in portal."""
    if not request.user.is_staff:
        messages.error(request, "Staff access only.")
        return redirect('/login')

    event = get_object_or_404(Event, slug=slug)
    query = request.GET.get('code', '').strip().upper()
    ticket = None
    action_result = None

    if query:
        ticket = Ticket.objects.filter(ticket_code=query, ticket_type__event=event).first()
        if not ticket:
            action_result = {'status': 'not_found', 'message': f"No ticket found for code: {query}"}
        else:
            if request.method == 'POST' and request.POST.get('action') == 'check_in':
                status, msg = check_in_ticket(ticket)
                action_result = {'status': status, 'message': msg}

    total_tickets = Ticket.objects.filter(ticket_type__event=event, order__status=TicketOrder.STATUS_PAID).count()
    checked_in_count = Ticket.objects.filter(ticket_type__event=event, checked_in=True).count()

    context = {
        'event': event,
        'query': query,
        'ticket': ticket,
        'action_result': action_result,
        'total_tickets': total_tickets,
        'checked_in_count': checked_in_count,
    }
    return render(request, 'ticketing/staff_checkin.html', context)
