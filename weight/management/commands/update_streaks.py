from django.core.management.base import BaseCommand
from weight.models import WeightLog
from weight.utils import update_streaks

class Command(BaseCommand):
    help = "Update Streaks of all users's logs in WeightLog table"

    def handle(self, *args, **options):
        # Inform when the process starts
        self.stdout.write("🚀 Starting Streaks update of all weight logs...")

        update_streaks()

        # Final message after update is complete
        self.stdout.write(self.style.SUCCESS(f"🎯 Successfully updated Streaks for logs."))
