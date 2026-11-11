import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.templatetags.static import static
from main.models import Event

User = get_user_model()


class Speaker(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='speakers')
    name = models.CharField(max_length=120)
    title_or_role = models.CharField(max_length=150, blank=True, help_text="e.g. Keynote Speaker / Tech Strategist")
    photo = models.ImageField(upload_to='events/speakers', blank=True)
    photo_static = models.CharField(max_length=200, blank=True,
                                    help_text="Static fallback path, e.g. images/events/speakers/evidence-akpah.jpg")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.name} ({self.event.title})"

    @property
    def photo_url(self):
        if self.photo:
            return self.photo.url
        if self.photo_static:
            return static(self.photo_static)
        return ''


class TicketType(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='ticket_types')
    name = models.CharField(max_length=80, default="Regular")
    description = models.CharField(max_length=255, blank=True, help_text="e.g. Access to all sessions + networking")
    price = models.PositiveIntegerField(default=5000, help_text="Price in Naira (NGN). Set 0 for free.")
    quantity = models.PositiveIntegerField(default=200, help_text="Total available seats")
    max_per_order = models.PositiveIntegerField(default=5)
    sales_start_date = models.DateTimeField(null=True, blank=True)
    sales_end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['price', 'id']

    def __str__(self):
        return f"{self.event.title} - {self.name} (₦{self.price:,})"

    @property
    def sold_count(self):
        return self.tickets.filter(order__status=TicketOrder.STATUS_PAID).count()

    @property
    def remaining(self):
        return max(0, self.quantity - self.sold_count)

    @property
    def is_available(self):
        if not self.is_active or self.remaining <= 0:
            return False
        now = timezone.now()
        if self.sales_start_date and now < self.sales_start_date:
            return False
        if self.sales_end_date and now > self.sales_end_date:
            return False
        return True


class TicketOrder(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_PAID = 'paid'
    STATUS_FAILED = 'failed'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = (
        (STATUS_PENDING, 'Pending'),
        (STATUS_PAID, 'Paid'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_CANCELLED, 'Cancelled'),
    )

    reference = models.CharField(max_length=64, unique=True, db_index=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='ticket_orders')
    ticket_type = models.ForeignKey(TicketType, on_delete=models.PROTECT, related_name='orders')
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.PositiveIntegerField(default=0)
    total_amount = models.PositiveIntegerField(default=0)

    # Buyer contact info
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='ticket_orders')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    paystack_reference = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.reference} - {self.full_name} ({self.status})"

    @classmethod
    def generate_reference(cls):
        return f"CAN-{uuid.uuid4().hex[:12].upper()}"


class Ticket(models.Model):
    order = models.ForeignKey(TicketOrder, on_delete=models.CASCADE, related_name='tickets')
    ticket_type = models.ForeignKey(TicketType, on_delete=models.PROTECT, related_name='tickets')
    ticket_code = models.CharField(max_length=32, unique=True, db_index=True)
    attendee_name = models.CharField(max_length=150)
    checked_in = models.BooleanField(default=False)
    checked_in_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"Ticket {self.ticket_code} - {self.attendee_name}"

    @classmethod
    def generate_code(cls):
        return f"TK-{uuid.uuid4().hex[:8].upper()}"

