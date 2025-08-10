# models.py
from dateutil.relativedelta import relativedelta
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from .managers import UserManager
# At the top of models.py

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(
        verbose_name="email address",
        max_length=255,
        unique=True,
    )
    name = models.CharField(max_length=50)
    phone = models.CharField(max_length=10)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name", "phone"]

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return self.is_admin

    def total_income(self):
        return sum([income.amount for income in self.income.all()]) if self.income.all() else 0
    
    def total_expense(self):
        return sum([expense.amount for expense in self.expenses.all()]) if self.expenses.all() else 0
    
    def total_savings(self):
        return self.total_income() - self.total_expense() if self.income.all() and self.expenses.all() else self.total_income()

# Rest of your models remain the same...
class Meta:
        # Add this Meta class to ensure proper model name
    verbose_name = 'user'
    verbose_name_plural = 'users'

class Category(models.Model):
    INCOME = 'Income'
    EXPENSE = 'Expense'
    CATEGORY_TYPES = [
        (INCOME, 'Income'),
        (EXPENSE, 'Expense'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name='categories')
    name = models.CharField(max_length=50)
    category_type = models.CharField(max_length=10, choices=CATEGORY_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.category_type})"

class Income(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='income')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        limit_choices_to={'category_type': 'Income'},
        related_name='income'
    )
    description = models.TextField(blank=True, null=True)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.name} - {self.category.name} - {self.amount}"

class Expense(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        limit_choices_to={'category_type': 'Expense'},
        related_name='expenses'
    )
    description = models.TextField(blank=True, null=True)
    date = models.DateField()
    is_fixed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.name} - {self.category.name} - {self.amount}"
        
# In models.py, add this class
class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='budgets')
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    amount_limit = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f"{self.user.name} - {self.category.name} Budget {self.amount_limit}"
    
    def get_spent_amount(self):
        return Expense.objects.filter(
            user=self.user,
            category=self.category,
            date__range=[self.start_date, self.end_date]
        ).aggregate(total=models.Sum('amount'))['total'] or 0
    
    def get_remaining_amount(self):
        spent = self.get_spent_amount()
        return self.amount_limit - spent
# models.py - Modified EMI model
class EMI(models.Model):
    FREQUENCY_CHOICES = [
        ('Daily', 'Daily'),
        ('Weekly', 'Weekly'),
        ('Monthly', 'Monthly'),
        ('Quarterly', 'Quarterly'),
        ('Semi-Annual', 'Semi-Annual'),
        ('Annual', 'Annual')
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='emis')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    description = models.TextField(blank=True, null=True)
    next_payment_date = models.DateField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.name} - EMI {self.amount} - {self.frequency}"

    def get_or_create_emi_category(self):
        """Get or create an EMI expense category"""
        emi_category, created = Category.objects.get_or_create(
            user=self.user,
            name="EMI",
            category_type='Expense',
            defaults={'name': 'EMI'}
        )
        return emi_category

    def create_expense(self):
        """Create an expense entry for the EMI payment if one doesn't already exist for this date"""
        # Check if an expense for this EMI already exists for today
        existing_expense = Expense.objects.filter(
            user=self.user,
            description=f"EMI Payment #{self.id} - {self.description}",
            date=self.next_payment_date
        ).first()
        
        if existing_expense:
            return existing_expense
        
        # Get or create the EMI category
        emi_category = self.get_or_create_emi_category()
        
        # Create a new expense if one doesn't exist
        expense = Expense.objects.create(
            user=self.user,
            amount=self.amount,
            category=emi_category,
            description=f"EMI Payment #{self.id} - {self.description}",
            date=self.next_payment_date,
            is_fixed=True
        )
        return expense
        
    def update_next_payment_date(self):
        """Update the next payment date based on frequency"""
        from dateutil.relativedelta import relativedelta
        
        if self.frequency == 'Daily':
            self.next_payment_date += relativedelta(days=1)
        elif self.frequency == 'Weekly':
            self.next_payment_date += relativedelta(weeks=1)
        elif self.frequency == 'Monthly':
            self.next_payment_date += relativedelta(months=1)
        elif self.frequency == 'Quarterly':
            self.next_payment_date += relativedelta(months=3)
        elif self.frequency == 'Semi-Annual':
            self.next_payment_date += relativedelta(months=6)
        elif self.frequency == 'Annual':
            self.next_payment_date += relativedelta(years=1)
        
        # If next payment date exceeds end date, mark EMI as inactive
        if self.next_payment_date > self.end_date:
            self.is_active = False
        
        self.save()
        
    def get_remaining_amount(self):
        """Calculate remaining amount to be paid"""
        paid_expenses = Expense.objects.filter(
            user=self.user,
            description__startswith=f"EMI Payment #{self.id} - ",
            date__range=[self.start_date, self.end_date]
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        
        return self.total_amount - paid_expenses