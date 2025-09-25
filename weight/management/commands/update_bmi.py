from django.core.management.base import BaseCommand
from weight.models import WeightLog
from weight.utils import calculate_bmi

class Command(BaseCommand):
    help = "Update BMIs of all users's logs in WeightLog table"

    def handle(self, *args, **options):
        # Inform when the process starts
        self.stdout.write("🚀 Starting BMI update of all weight logs...")

        # Fetch all WeightLog records where weight is not null
        logs = WeightLog.objects.exclude(weight__isnull=True)
        total_logs = logs.count()
        self.stdout.write(f"ℹ️  Found {total_logs} weight logs to update.")

        updated_count = 0

        for log in logs:
            height = log.profile.height_cm
            weight = log.weight

            # Print current processing log
            print(f"🔧 Processing log ID: {log.id}, Weight: {weight} kg, Height: {height} cm")

            # Calculate BMI using utility function
            bmi_data = calculate_bmi(weight, height)
            log.bmi = bmi_data.get("value")

            print(f"✅ Updated BMI for log ID {log.id}: {bmi_data}")

            updated_count += 1

        # Perform bulk update for performance
        WeightLog.objects.bulk_update(logs, ['bmi'], batch_size=100)

        # Final message after update is complete
        self.stdout.write(self.style.SUCCESS(f"🎯 Successfully updated BMI for {updated_count} logs."))
