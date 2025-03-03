from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_date
from datetime import datetime, timedelta
from windshields.models import TimeSlot
from windshields.models import ShopSetting

class Command(BaseCommand):
    help = "Populate timeslots for a given shop between two dates."

    def add_arguments(self, parser):
        parser.add_argument('shop_id', type=int, help="ID of the shop")
        parser.add_argument('start_date', type=str, help="Start date in YYYY-MM-DD")
        parser.add_argument('end_date', type=str, help="End date in YYYY-MM-DD")

    def handle(self, *args, **options):
        shop_id = options['shop_id']
        start_date = parse_date(options['start_date'])
        end_date = parse_date(options['end_date'])
        try:
            shop = ShopSetting.objects.get(id=shop_id)
        except ShopSetting.DoesNotExist:
            self.stdout.write(self.style.ERROR("Shop not found."))
            return

        hours = shop.hours_of_operation  # Assuming it's a dict mapping weekday names to [start, end] times.
        current_date = start_date
        while current_date <= end_date:
            weekday = current_date.strftime("%A")
            if weekday in hours:
                start_str, end_str = hours[weekday]
                start_time = datetime.strptime(start_str, "%H:%M").time()
                end_time = datetime.strptime(end_str, "%H:%M").time()
                dt = datetime.combine(current_date, start_time)
                end_dt = datetime.combine(current_date, end_time)
                while dt + timedelta(minutes=30) <= end_dt:
                    slot_start = dt.time()
                    slot_end = (dt + timedelta(minutes=30)).time()
                    # Create the timeslot if it doesn't already exist.
                    TimeSlot.objects.get_or_create(
                        date=current_date,
                        start_time=slot_start,
                        end_time=slot_end,
                        defaults={'filled': False}
                    )
                    dt += timedelta(minutes=30)
            current_date += timedelta(days=1)
        self.stdout.write(self.style.SUCCESS("Timeslots populated."))
