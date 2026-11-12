import io
import logging
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from main.models import Event
from main.Paystack import PayStack
from .models import TicketType, TicketOrder, Ticket

logger = logging.getLogger(__name__)


class TicketServiceError(Exception):
    """Domain exception for ticketing service errors."""
    pass


def create_ticket_order(event, ticket_type, quantity, full_name, email, phone, user=None):
    """
    Validate inventory, clean attendee data, and create a pending TicketOrder.
    """
    if not full_name or not email or not phone:
        raise TicketServiceError("Please fill in your name, email, and phone number.")

    try:
        quantity = int(quantity)
    except (ValueError, TypeError):
        quantity = 1

    if quantity < 1:
        quantity = 1
    if quantity > ticket_type.max_per_order:
        quantity = ticket_type.max_per_order

    if ticket_type.remaining < quantity:
        raise TicketServiceError(f"Sorry, only {ticket_type.remaining} tickets remain for {ticket_type.name}.")

    total_amount = ticket_type.price * quantity
    reference = TicketOrder.generate_reference()

    order = TicketOrder.objects.create(
        reference=reference,
        event=event,
        ticket_type=ticket_type,
        quantity=quantity,
        unit_price=ticket_type.price,
        total_amount=total_amount,
        full_name=full_name.strip(),
        email=email.strip().lower(),
        phone=phone.strip(),
        user=user if user and user.is_authenticated else None,
        status=TicketOrder.STATUS_PENDING,
    )
    return order


def initiate_paystack_checkout(order, callback_url):
    """
    Initiate checkout with Paystack for a given pending order.
    Returns the redirect URL string or None if connection fails.
    """
    metadata = {
        'transaction_type': 'event_ticket',
        'order_reference': order.reference,
        'event_slug': order.event.slug,
        'quantity': order.quantity,
    }

    return PayStack.generate_checkout_url(
        email=order.email,
        amount=order.total_amount * 100,  # Paystack expects amount in kobo
        ref=order.reference,
        currency='NGN',
        metadata=metadata,
        callback_url=callback_url,
    )


@transaction.atomic
def fulfil_ticket_order(order, paystack_ref=""):
    """
    Idempotently issue tickets, mark order as paid, and record timestamps with row locking.
    """
    locked_order = TicketOrder.objects.select_for_update().get(id=order.id)
    if locked_order.status == TicketOrder.STATUS_PAID:
        return locked_order

    locked_order.status = TicketOrder.STATUS_PAID
    locked_order.paid_at = timezone.now()
    if paystack_ref:
        locked_order.paystack_reference = paystack_ref
    locked_order.save()

    # Create individual tickets if not yet created
    if not locked_order.tickets.exists():
        for i in range(locked_order.quantity):
            attendee = locked_order.full_name
            if locked_order.quantity > 1:
                attendee = f"{locked_order.full_name} (Guest {i+1})"
            Ticket.objects.create(
                order=locked_order,
                ticket_type=locked_order.ticket_type,
                ticket_code=Ticket.generate_code(),
                attendee_name=attendee,
            )

    # Dispatch confirmation email with attached PDF ticket pass
    send_ticket_confirmation_email(locked_order)

    return locked_order


def send_ticket_confirmation_email(order):
    """
    Render and send ticket confirmation email with attached PDF pass.
    Catches all exceptions so an SMTP failure never prevents order completion.
    """
    try:
        subject = f"Your Tickets for {order.event.title} [Ref: {order.reference}]"
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', getattr(settings, 'EMAIL_HOST_USER', 'send@churcharisenetwork.com.ng'))
        to_email = [order.email]

        context = {'order': order}
        html_content = render_to_string('ticketing/emails/ticket_confirmation.html', context)
        text_content = strip_tags(html_content)

        msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
        msg.attach_alternative(html_content, "text/html")

        # Generate and attach PDF pass
        pdf_buffer = generate_ticket_pdf(order)
        msg.attach(f"tickets-{order.reference}.pdf", pdf_buffer.getvalue(), "application/pdf")

        msg.send(fail_silently=False)
        logger.info("Successfully sent ticket confirmation email to %s for order %s", order.email, order.reference)
        return True
    except Exception as e:
        logger.error("Failed to send ticket confirmation email to %s for order %s: %s", order.email, order.reference, e, exc_info=True)
        return False


def verify_and_fulfil_order(reference):
    """
    Verify payment status with Paystack and fulfil the order.
    Returns (success: bool, order: TicketOrder or None, error_message: str or None).
    """
    order = TicketOrder.objects.filter(reference=reference).first()
    if not order:
        return False, None, "Order record not found."

    # Idempotent return if already paid
    if order.status == TicketOrder.STATUS_PAID:
        return True, order, None

    payment_info = PayStack.verify_payment(reference)
    if not payment_info or payment_info.get('status') != 'success':
        return False, order, "Payment could not be verified or was cancelled."

    paid_amount_kobo = payment_info.get('amount', 0)
    expected_amount_kobo = order.total_amount * 100

    if paid_amount_kobo < expected_amount_kobo:
        logger.error("Paid amount mismatch: paid %s kobo, expected %s kobo", paid_amount_kobo, expected_amount_kobo)
        order.status = TicketOrder.STATUS_FAILED
        order.save()
        return False, order, "Payment verification error: amount paid does not match ticket total."

    fulfilled_order = fulfil_ticket_order(order, paystack_ref=reference)
    return True, fulfilled_order, None


def generate_ticket_pdf(order):
    """
    Build printable PDF tickets using ReportLab and return an in-memory BytesIO buffer.
    """
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.graphics.shapes import Drawing
    from reportlab.graphics.barcode.qr import QrCodeWidget

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'TicketTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#29285d')
    )
    theme_style = ParagraphStyle(
        'TicketTheme',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#469bd8')
    )
    label_style = ParagraphStyle('Label', fontName='Helvetica-Bold', fontSize=9, textColor=colors.HexColor('#6b7280'))
    val_style = ParagraphStyle('Val', fontName='Helvetica', fontSize=10, textColor=colors.HexColor('#111827'))

    tickets = order.tickets.all()
    for idx, ticket in enumerate(tickets):
        if idx > 0:
            elements.append(Spacer(1, 24))

        # QR Widget
        qr = QrCodeWidget(f"TICKET:{ticket.ticket_code}|EVENT:{order.event.slug}|NAME:{ticket.attendee_name}")
        d = Drawing(100, 100)
        d.add(qr)

        info_text = f"""
        <b>Attendee:</b> {ticket.attendee_name}<br/>
        <b>Ticket Tier:</b> {ticket.ticket_type.name}<br/>
        <b>Ticket Code:</b> <font color="#29285d"><b>{ticket.ticket_code}</b></font><br/>
        <b>Order Ref:</b> {order.reference}<br/>
        <b>Date & Time:</b> {order.event.event_date.strftime('%B %d, %Y at %I:%M %p')}<br/>
        <b>Location:</b> {order.event.venue or 'Venue'} {order.event.city}<br/>
        <b>Enquiries:</b> {order.event.enquiry_phone}
        """

        card_data = [
            [
                Paragraph(f"<b>{order.event.title}</b>", title_style),
                Paragraph(f"<b>{order.event.presenter}</b>", val_style)
            ],
            [
                Paragraph(f"<i>Theme: {order.event.theme}</i>", theme_style),
                ""
            ],
            [
                Paragraph(info_text, val_style),
                d
            ]
        ]

        t = Table(card_data, colWidths=[380, 160])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('PADDING', (0, 0), (-1, -1), 12),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('SPAN', (0, 1), (1, 1)),
        ]))
        elements.append(t)

    doc.build(elements)
    buffer.seek(0)
    return buffer


def check_in_ticket(ticket):
    """
    Perform check-in action for a ticket.
    Returns (status: str, message: str).
    """
    if ticket.checked_in:
        return 'already', f"Ticket was ALREADY checked in at {ticket.checked_in_at.strftime('%I:%M %p')}!"

    ticket.checked_in = True
    ticket.checked_in_at = timezone.now()
    ticket.save()
    return 'success', f"Successfully checked in {ticket.attendee_name}!"

