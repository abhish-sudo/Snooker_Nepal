from django.db import models
from django.utils import timezone


class Tournament(models.Model):
    STATUS_CHOICES = [
        ('upcoming',  'Upcoming'),
        ('ongoing',   'Ongoing'),
        ('completed', 'Completed'),
    ]
    FORMAT_CHOICES = [
        ('open',         'Open'),
        ('ranking',      'Ranking'),
        ('invitational', 'Invitational'),
        ('club',         'Club Level'),
    ]
    CATEGORY_CHOICES = [
        ('open',      'Open'),
        ('u21',       'Under 21'),
        ('veterans',  'Veterans 40+'),
        ('ladies',    'Ladies'),
    ]

    name                  = models.CharField(max_length=200)
    format                = models.CharField(max_length=20, choices=FORMAT_CHOICES, default='open')
    category              = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='open')
    status                = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')
    city                  = models.CharField(max_length=100)
    venue_name            = models.CharField(max_length=200)
    venue_map_link        = models.URLField(blank=True, help_text='Google Maps link to venue')
    start_date            = models.DateField(null=True, blank=True)
    end_date              = models.DateField(null=True, blank=True)
    registration_deadline = models.DateField(null=True, blank=True)
    entry_fee             = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    prize_money           = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    description           = models.TextField(blank=True)
    poster                = models.ImageField(upload_to='tournaments/posters/', null=True, blank=True)
    contact_phone         = models.CharField(max_length=20, help_text='WhatsApp number (without +977)')
    max_players           = models.PositiveIntegerField(default=32)
    is_approved           = models.BooleanField(default=False)
    created_at            = models.DateTimeField(auto_now_add=True)
    is_coming_soon        = models.BooleanField(
                                default=False,
                                help_text='Tick if exact dates are not yet confirmed'
                            )

    class Meta:
        ordering = ['start_date']

    def __str__(self):
        return self.name

    def spots_left(self):
        return max(0, self.max_players - self.registrations.count())

    def is_registration_open(self):
        if self.is_coming_soon:
            return False
        if not self.registration_deadline:
            return False
        today = timezone.now().date()
        return (
            self.status == 'upcoming'
            and today <= self.registration_deadline
            and self.spots_left() > 0
        )

    def registration_percentage(self):
        if self.max_players == 0:
            return 0
        taken = self.registrations.count()
        return min(100, int((taken / self.max_players) * 100))


class Registration(models.Model):
    tournament         = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='registrations')
    full_name          = models.CharField(max_length=100)
    phone              = models.CharField(max_length=15)
    city               = models.CharField(max_length=100)
    age                = models.PositiveIntegerField()
    club_or_hall       = models.CharField(max_length=100, blank=True, help_text='Optional')
    payment_screenshot = models.ImageField(
        upload_to='tournaments/payments/',
        null=True, blank=True,
        help_text='Upload eSewa / Khalti screenshot if entry fee applies'
    )
    registered_at      = models.DateTimeField(auto_now_add=True)
    is_paid            = models.BooleanField(default=False)

    class Meta:
        ordering = ['registered_at']
        unique_together = ['tournament', 'phone']

    def __str__(self):
        return f'{self.full_name} — {self.tournament.name}'