from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='WikiPage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.SlugField(unique=True)),
                ('title', models.CharField(max_length=200)),
                ('content', models.TextField(help_text='Markdown content')),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['title'],
            },
        ),
    ]
