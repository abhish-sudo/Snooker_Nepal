from django.core.management.base import BaseCommand
from django.utils import timezone
from tournaments.models import Tournament


class Command(BaseCommand):
    help = 'Auto-update tournament statuses based on today\'s date'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()

        ongoing = Tournament.objects.filter(
            start_date__lte=today,
            end_date__gte=today,
            is_approved=True
        ).exclude(status='ongoing').update(status='ongoing')

        completed = Tournament.objects.filter(
            end_date__lt=today,
            is_approved=True
        ).exclude(status='completed').update(status='completed')

        self.stdout.write(
            self.style.SUCCESS(
                f'Updated: {ongoing} → ongoing, {completed} → completed'
            )
        )