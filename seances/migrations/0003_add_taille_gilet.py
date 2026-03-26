from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('seances', '0002_alter_reservation_statut'),
    ]

    operations = [
        migrations.AddField(
            model_name='reservation',
            name='taille_gilet',
            field=models.CharField(choices=[('XS', 'XS'), ('S', 'S'), ('M', 'M'), ('L', 'L'), ('XL', 'XL')], max_length=3, null=True, blank=True, default=None),
        ),
    ]
