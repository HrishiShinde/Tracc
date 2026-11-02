import base64

from django.core.management.base import BaseCommand
from cryptography.hazmat.primitives import serialization
from py_vapid import Vapid


class Command(BaseCommand):
    help = "Generate a VAPID key pair for Web Push and print it once."

    def handle(self, *args, **options):
        vapid = Vapid()
        vapid.generate_keys()
        private_raw = vapid.private_key.private_numbers().private_value.to_bytes(32, "big")
        public_raw = vapid.public_key.public_bytes(
            serialization.Encoding.X962,
            serialization.PublicFormat.UncompressedPoint,
        )
        encode = lambda value: base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")
        self.stdout.write(f"VAPID_PUBLIC_KEY={encode(public_raw)}")
        self.stdout.write(f"VAPID_PRIVATE_KEY={encode(private_raw)}")
        self.stdout.write(self.style.WARNING("Store the private key as a secret. Generating a new pair invalidates existing browser subscriptions."))
