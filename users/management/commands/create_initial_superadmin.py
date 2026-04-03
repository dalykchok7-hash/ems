# yourapp/management/commands/create_initial_superadmin.py

from django.core.management.base import BaseCommand
from users.models import Utilisateur

class Command(BaseCommand):
    help = "Create initial superadmin dynamically from CLI"

    def add_arguments(self, parser):
        parser.add_argument("--username", required=True, help="Username")
        parser.add_argument("--email", required=True, help="Email")
        parser.add_argument("--password", required=True, help="Password")

    def handle(self, *args, **options):
        username = options["username"]
        email = options["email"]
        password = options["password"]

        if Utilisateur.objects.filter(role="admin").exists():
            self.stdout.write(self.style.WARNING("Superadmin already exists"))
            return

        user = Utilisateur.objects.create_user(
            username=username,
            email=email,
            password=password,
            role="admin"
        )

        # Optional: sync with Django admin privileges
        user.is_staff = True
        user.is_superuser = True
        user.save()

        self.stdout.write(self.style.SUCCESS(f"admin '{username}' created successfully"))