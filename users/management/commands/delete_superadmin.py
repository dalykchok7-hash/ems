from django.core.management.base import BaseCommand
from users.models import Utilisateur

class Command(BaseCommand):
    help = "Delete superadmin user(s)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            type=str,
            help="Delete a specific superadmin by username"
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Delete all superadmins"
        )

    def handle(self, *args, **options):
        username = options.get("username")
        delete_all = options.get("all")

        if not username and not delete_all:
            self.stdout.write(self.style.ERROR(
                "You must provide --username or --all"
            ))
            return

        if delete_all:
            qs = Utilisateur.objects.filter(role="admin")
            count = qs.count()
            qs.delete()
            self.stdout.write(self.style.SUCCESS(
                f"{count} admin(s) deleted"
            ))
            return

        try:
            user = Utilisateur.objects.filter(username=username, role="admin")
            user.delete()
            self.stdout.write(self.style.SUCCESS(
                f"admin '{username}' deleted"
            ))
        except Utilisateur.DoesNotExist:
            self.stdout.write(self.style.WARNING(
                "admin not found"
            ))