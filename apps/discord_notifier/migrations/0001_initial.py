from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='DiscordPostedMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ranking_id', models.CharField(max_length=32, unique=True)),
                ('message_id', models.CharField(max_length=32)),
                ('posted_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
