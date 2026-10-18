import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Doctor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120)),
                ('specialty', models.CharField(blank=True, max_length=120)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Patient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120)),
                ('phone', models.CharField(max_length=32)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Appointment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_time', models.DateTimeField(db_index=True)),
                ('end_time', models.DateTimeField()),
                ('status', models.CharField(choices=[('booked', 'Booked'), ('cancelled', 'Cancelled')], default='booked', max_length=12)),
                ('notes', models.CharField(blank=True, max_length=500)),
                ('cancel_reason', models.CharField(blank=True, max_length=500)),
                ('cancelled_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('doctor', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='appointments', to='clinic.doctor')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='appointments', to='clinic.patient')),
            ],
            options={
                'ordering': ['start_time'],
                'indexes': [models.Index(fields=['patient', 'status', 'start_time'], name='appt_patient_upcoming_idx')],
                'constraints': [models.UniqueConstraint(condition=models.Q(('status', 'booked')), fields=('doctor', 'start_time'), name='uniq_booked_slot_per_doctor'), models.CheckConstraint(condition=models.Q(('start_time__lt', models.F('end_time'))), name='appointment_start_before_end')],
            },
        ),
        migrations.CreateModel(
            name='WorkingHours',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('weekday', models.PositiveSmallIntegerField(choices=[(0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'), (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday')])),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('doctor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='working_hours', to='clinic.doctor')),
            ],
            options={
                'verbose_name_plural': 'working hours',
                'ordering': ['doctor_id', 'weekday', 'start_time'],
                'constraints': [models.CheckConstraint(condition=models.Q(('start_time__lt', models.F('end_time'))), name='working_hours_start_before_end'), models.UniqueConstraint(fields=('doctor', 'weekday', 'start_time'), name='uniq_working_block')],
            },
        ),
    ]
