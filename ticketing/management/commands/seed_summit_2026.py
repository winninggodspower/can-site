from datetime import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from main.models import Event
from ticketing.models import TicketType, Speaker


class Command(BaseCommand):
    help = 'Seeds or updates the Business Tech Summit 2026 event, speakers, and ticket tiers.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding Business Tech Summit 2026..."))

        event, created = Event.objects.get_or_create(
            slug='business-tech-summit-2026',
            defaults={
                'title': 'Business Tech Summit 2026',
                'theme': 'Scaling Productivity in an Era of Convergent Technology',
                'presenter': 'Life for Generations®',
                'breif_description': 'Join visionary leaders, entrepreneurs, and technology pioneers in Port Harcourt to explore business outlook, growth strategies, and enterprise pitching.',
                'event_date': timezone.make_aware(datetime(2026, 12, 19, 9, 0, 0)),
                'registration_start_date': datetime(2026, 11, 1).date(),
                'registration_end_date': datetime(2026, 12, 18).date(),
                'venue': 'To be announced',
                'city': 'Port Harcourt, Rivers State',
                'enquiry_phone': '+234 904 778 2811',
                'highlights': """Business outlook for 2027
Strategies for business growth
Pitching to potential clients and partners
Networking with the business community""",
                'flyer_static': 'images/events/business-tech-summit-2026.jpg',
                'is_featured': True,
                'ticketing_enabled': True,
            }
        )

        if not created:
            event.title = 'Business Tech Summit 2026'
            event.theme = 'Scaling Productivity in an Era of Convergent Technology'
            event.presenter = 'Life for Generations®'
            event.breif_description = 'Join visionary leaders, entrepreneurs, and technology pioneers in Port Harcourt to explore business outlook, growth strategies, and enterprise pitching.'
            event.venue = 'To be announced'
            event.city = 'Port Harcourt, Rivers State'
            event.enquiry_phone = '+234 904 778 2811'
            event.highlights = """Business outlook for 2027
Strategies for business growth
Pitching to potential clients and partners
Networking with the business community"""
            event.flyer_static = 'images/events/business-tech-summit-2026.jpg'
            event.is_featured = True
            event.ticketing_enabled = True
            event.save()
            self.stdout.write(self.style.SUCCESS("  ✓ Updated Event details"))
        else:
            self.stdout.write(self.style.SUCCESS("  ✓ Created Event: Business Tech Summit 2026"))

        # Default Regular ticket tier
        ticket_type, t_created = TicketType.objects.get_or_create(
            event=event,
            name='Regular',
            defaults={
                'price': 5000,
                'quantity': 250,
                'description': 'Full summit pass with access to all keynote sessions and business community networking.'
            }
        )
        if t_created:
            self.stdout.write(self.style.SUCCESS("  ✓ Created Regular Ticket tier (₦5,000)"))
        else:
            self.stdout.write(self.style.SUCCESS("  ✓ Ticket tier exists"))

        # Speakers list
        speakers_data = [
            ('ThankGod Ukeh', 'Host', 'images/events/speakers/thankgod-ukeh.jpg', 1),
            ('Evidence Akpah', 'Speaker', 'images/events/speakers/evidence-akpah.jpg', 2),
            ('Dr. Lynn Ujiagbe', 'Speaker', 'images/events/speakers/lynn-ujiagbe.jpg', 3),
            ('Favour Chinonso', 'Speaker', 'images/events/speakers/favour-chinonso.jpg', 4),
            ('Ben Bright', 'Speaker', 'images/events/speakers/ben-bright.jpg', 5),
            ('Ronald Kenneth', 'Speaker', 'images/events/speakers/ronald-kenneth.jpg', 6),
        ]

        for name, role, photo_static, order in speakers_data:
            Speaker.objects.update_or_create(
                event=event,
                name=name,
                defaults={
                    'title_or_role': role,
                    'photo_static': photo_static,
                    'order': order,
                }
            )

        self.stdout.write(self.style.SUCCESS(f"  ✓ Seeded {len(speakers_data)} speakers"))
        self.stdout.write(self.style.SUCCESS("Business Tech Summit 2026 is fully ready on production!"))

