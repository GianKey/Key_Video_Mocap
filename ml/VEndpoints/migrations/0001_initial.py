# Generated by Django 4.2.5 on 2024-01-22 21:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('video', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='VEndpoint',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
                ('owner', models.CharField(max_length=128)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='VMLAlgorithm',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
                ('description', models.CharField(max_length=1000)),
                ('code', models.TextField(max_length=50000)),
                ('version', models.CharField(max_length=128)),
                ('owner', models.CharField(max_length=128)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('parent_endpoint', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='VEndpoints.vendpoint')),
            ],
        ),
        migrations.CreateModel(
            name='VMLRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('input_data', models.FileField(max_length=255, upload_to='')),
                ('full_response', models.TextField(max_length=10000)),
                ('response', models.TextField(max_length=10000)),
                ('feedback', models.TextField(blank=True, max_length=10000, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('parent_mlalgorithm', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='VEndpoints.vmlalgorithm')),
                ('related_Video', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='video.video')),
            ],
        ),
        migrations.CreateModel(
            name='VMLAlgorithmStatus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(max_length=128)),
                ('active', models.BooleanField()),
                ('created_by', models.CharField(max_length=128)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('parent_mlalgorithm', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='status', to='VEndpoints.vmlalgorithm')),
            ],
        ),
    ]
