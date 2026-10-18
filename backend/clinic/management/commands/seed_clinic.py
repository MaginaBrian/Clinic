from datetime import time

from django.core.management.base import BaseCommand

from clinic.models import Doctor, WorkingHours

MON_FRI = range(0, 5)

DOCTORS = [
    ("Dr. Amina Odhiambo", "General practice", [(MON_FRI, time(9), time(12, 30)), (MON_FRI, time(14), time(17))]),
    ("Dr. Brian Kamau", "Paediatrics", [(MON_FRI, time(8), time(13))]),
    ("Dr. Chebet Rotich", "Women's health", [(range(0, 4), time(10), time(13)), (range(0, 4), time(14), time(18))]),
    ("Dr. David Mwangi", "Dermatology", [(MON_FRI, time(9), time(17)), ([5], time(9), time(12))]),
    ("Dr. Esther Njeri", "Family medicine", [(range(1, 6), time(8, 30), time(12, 30)), (range(1, 5), time(14), time(16, 30))]),
]


class Command(BaseCommand):
    help = "Create the clinic's 5 doctors and their weekly hours (idempotent)."

    def handle(self, *args, **options):
        for name, specialty, blocks in DOCTORS:
            doctor, created = Doctor.objects.get_or_create(name=name, defaults={"specialty": specialty})
            for weekdays, start, end in blocks:
                for wd in weekdays:
                    WorkingHours.objects.get_or_create(
                        doctor=doctor, weekday=wd, start_time=start, defaults={"end_time": end}
                    )
            self.stdout.write(f"{'created' if created else 'ok     '} {name}")
