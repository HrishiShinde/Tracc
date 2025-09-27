from django.core.management.base import BaseCommand
from weight.utils import (
    seed_milestones,
    update_all_bmis,
    update_streaks,
)

class Command(BaseCommand):
    help = "Sync milestones seeding, BMI updates, and streak updates (all or specific one)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--only",
            type=str,
            choices=["milestones", "bmi", "streaks"],
            help="Run only a specific task instead of all."
        )

    def handle(self, *args, **options):
        only = options.get("only")

        if only in [None, "milestones"]:
            self.stdout.write("🌱 Seeding milestones…")
            seed_milestones()
            self.stdout.write(self.style.SUCCESS("✅ Milestones seeded."))

        if only in [None, "bmi"]:
            self.stdout.write("📊 Updating BMIs…")
            update_all_bmis()
            self.stdout.write(self.style.SUCCESS("✅ BMI update done."))

        if only in [None, "streaks"]:
            self.stdout.write("🔥 Updating streaks…")
            update_streaks()
            self.stdout.write(self.style.SUCCESS("✅ Streaks updated."))
