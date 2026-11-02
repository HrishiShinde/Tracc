from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from pywebpush import WebPushException, webpush

from weight.models import PushReminderDelivery, Settings as UserSettings


class Command(BaseCommand):
    help = "Send due daily weight reminders to users who have not checked in."

    def handle(self, *args, **options):
        private_key = getattr(settings, "VAPID_PRIVATE_KEY", "")
        public_key = getattr(settings, "VAPID_PUBLIC_KEY", "")
        contact_email = getattr(settings, "VAPID_CONTACT_EMAIL", "")
        if not private_key or not public_key or not contact_email:
            raise CommandError("VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY, and VAPID_CONTACT_EMAIL must be configured.")

        now = timezone.now()
        sent = 0
        subscriptions = UserSettings.objects.filter(daily_log=True).exclude(reminder_time=None).select_related("user__profile")
        for user_settings in subscriptions.iterator():
            profile = user_settings.user.profile
            try:
                local_now = now.astimezone(ZoneInfo(profile.time_zone or "UTC"))
            except ZoneInfoNotFoundError:
                local_now = now.astimezone(ZoneInfo("UTC"))

            reminder_time = user_settings.reminder_time
            if (local_now.hour, local_now.minute) != (reminder_time.hour, reminder_time.minute):
                continue
            if profile.weightlog_set.filter(date=local_now.date(), check_in=True).exists():
                continue
            if PushReminderDelivery.objects.filter(profile=profile, reminder_date=local_now.date()).exists():
                continue

            payload = '{"title":"Time to check in","body":"Your daily weight check-in is waiting.","url":"/dashboard/"}'
            delivered = False
            for subscription in user_settings.user.push_subscriptions.all():
                try:
                    webpush(
                        subscription_info={
                            "endpoint": subscription.endpoint,
                            "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
                        },
                        data=payload,
                        vapid_private_key=private_key,
                        vapid_claims={"sub": f"mailto:{contact_email}"},
                    )
                    delivered = True
                except WebPushException as exc:
                    status = getattr(getattr(exc, "response", None), "status_code", None)
                    if status in (404, 410):
                        subscription.delete()
                    else:
                        self.stderr.write(f"Push failed for user {user_settings.user_id}: {exc}")

            if delivered:
                PushReminderDelivery.objects.get_or_create(profile=profile, reminder_date=local_now.date())
                sent += 1

        self.stdout.write(self.style.SUCCESS(f"Sent daily reminders to {sent} user(s)."))
