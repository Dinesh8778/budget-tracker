# in myapp/management/commands/process_emi_payments.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from myapp.models import EMI
from datetime import date

class Command(BaseCommand):
    help = 'Process due EMI payments and create expense entries'

    def handle(self, *args, **options):
        # Get today's date
        today = date.today()
        
        # Find all active EMIs where the next payment date is today or earlier
        due_emis = EMI.objects.filter(
            is_active=True,
            next_payment_date__lte=today
        )
        
        processed_count = 0
        
        for emi in due_emis:
            try:
                # Create an expense entry for this EMI
                expense = emi.create_expense()
                
                # Update the next payment date for this EMI
                emi.update_next_payment_date()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully processed EMI payment: {emi.description} - ${emi.amount}'
                    )
                )
                processed_count += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Error processing EMI {emi.id}: {str(e)}'
                    )
                )
        
        if processed_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully processed {processed_count} EMI payments'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    'No EMI payments due for processing today'
                )
            )