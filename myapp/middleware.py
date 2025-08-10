# myapp/middleware.py
from django.utils import timezone
from .models import EMI, Expense

class EMIPaymentMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Process EMI payments only for authenticated users
        if request.user.is_authenticated:
            self.process_due_emi_payments(request)
        
        response = self.get_response(request)
        return response
    
    def process_due_emi_payments(self, request):
        """Process all due EMI payments and create corresponding expense entries"""
        today = timezone.now().date()
        due_emis = EMI.objects.filter(
            user=request.user,
            is_active=True,
            next_payment_date__lte=today
        )
        
        for emi in due_emis:
            # Create expense entry for this payment
            expense = emi.create_expense()
            
            # Update the next payment date
            emi.update_next_payment_date()