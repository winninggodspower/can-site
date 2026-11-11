from django.db import models
from django.contrib.auth.models import User
from cloudinary_storage.storage import RawMediaCloudinaryStorage
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone

# Create your models here.
class About(models.Model):
    organization_name            = models.CharField(max_length=50)
    organization_mailer_address  = models.EmailField(max_length=254)
    organization_mailer_password = models.CharField(max_length=100)
    body                         = models.TextField()

class Announcement(models.Model):
    image       = models.ImageField( upload_to='announcement', )
    headline    = models.CharField(max_length=100)
    body        = models.TextField()
    action_url  = models.URLField(max_length=300, null=True, blank=True)
    action_text = models.CharField(max_length=10, null=True, blank=True)

    def __str__(self):
        return self.headline

class Gallery(models.Model):
    image       = models.ImageField( upload_to='gallery', )
    title       = models.CharField(max_length=100)

    def __str__(self):
        return self.title

class Giving(models.Model):
    amount = models.PositiveIntegerField()
    message = models.TextField(null=True, blank=True)


class MeetingReport(models.Model):
    date = models.DateField()
    partners_name = models.CharField(max_length=255) 
    moderator = models.CharField(max_length=255)
    city_nation = models.CharField(max_length=255)
    prayer_request = models.TextField()
    general_comment = models.TextField()

    def __str__(self):
        return self.general_comment[0: 10]
    
class Welfare(models.Model):
    member_name = models.CharField(max_length=100)
    details = models.TextField()
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.member_name + ": " + self.details[0: 10]

class Publication(models.Model):
    image        = models.ImageField( upload_to='publication', )
    headline     = models.CharField(max_length=100)
    fontawesome_class      = models.CharField(max_length=50, default='fa-user-graduate')
    description  = models.TextField()
    file         = models.FileField(
        upload_to='publication_files',
        storage=RawMediaCloudinaryStorage(),
    )
    price        = models.PositiveIntegerField(default=0)
    uploadedAt   = models.DateTimeField(auto_now_add=True, db_column='uploadedat')

    def __str__(self):
        return self.headline
    
class PublicationPayment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE)
    payment_date = models.DateTimeField(auto_now_add=True)
    approved     = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} paid for- {self.publication.headline}"
    

class Event(models.Model):
    title = models.CharField(max_length=80)
    slug = models.SlugField(max_length=90, unique=True, null=True, blank=True,
                            help_text="Used in the event page URL, e.g. business-tech-summit-2026")
    banner = models.ImageField(upload_to='events', blank=True)
    breif_description = models.CharField(max_length=200)
    event_date = models.DateTimeField()
    registration_start_date = models.DateField(blank=True, null=True)
    registration_end_date = models.DateField(blank=True, null=True)
    registration_url = models.URLField(max_length=200, blank=True,
                                       help_text="External registration link. Ignored when ticketing is enabled.")

    # Featured / ticketed event details
    theme = models.CharField(max_length=200, blank=True)
    presenter = models.CharField(max_length=100, blank=True, help_text='e.g. "Life for Generations®"')
    venue = models.CharField(max_length=200, blank=True, help_text="Leave blank to show 'Venue to be announced'")
    city = models.CharField(max_length=100, blank=True)
    enquiry_phone = models.CharField(max_length=30, blank=True)
    highlights = models.TextField(blank=True, help_text="What attendees get. One item per line.")
    flyer = models.ImageField(upload_to='events/flyers', blank=True)
    flyer_static = models.CharField(max_length=200, blank=True,
                                    help_text="Static file path used when no flyer is uploaded, "
                                              "e.g. images/events/business-tech-summit-2026.jpg")
    is_featured = models.BooleanField(default=False,
                                      help_text="Show this event in the featured section on the home page")
    ticketing_enabled = models.BooleanField(default=False,
                                            help_text="Sell tickets on this site instead of linking out")

    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    @property
    def flyer_url(self):
        if self.flyer:
            return self.flyer.url
        if self.flyer_static:
            return static(self.flyer_static)
        return ''

    @property
    def cover_url(self):
        """Best available image for cards: banner first, then the flyer."""
        if self.banner:
            return self.banner.url
        return self.flyer_url

    @property
    def highlight_list(self):
        return [line.strip() for line in self.highlights.splitlines() if line.strip()]

    @property
    def is_past(self):
        return self.event_date <= timezone.now()

    def get_absolute_url(self):
        if self.ticketing_enabled and self.slug:
            return reverse('ticketing:event_detail', kwargs={'slug': self.slug})
        return self.registration_url or reverse('event')
