from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.core.exceptions import ValidationError
from .models import User, Category, Income, Expense,Budget,EMI

class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(
        label="Password confirmation", widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = ["name", "email", "phone"]

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = ["name", "email", "password", "phone", "is_active", "is_admin"]

# Add new forms below

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'category_type']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500'}),
            'category_type': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500'}),
        }

class IncomeForm(forms.ModelForm):
    class Meta:
        model = Income
        fields = ['amount', 'category', 'description', 'date']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500', 'step': '0.01'}),
            'category': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500', 'rows': 3}),
            'date': forms.DateInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500', 'type': 'date'}),
        }

    def __init__(self, user, *args, **kwargs):
        super(IncomeForm, self).__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(user=user, category_type='Income')

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['amount', 'category', 'description', 'date', 'is_fixed']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500', 'step': '0.01'}),
            'category': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500', 'rows': 3}),
            'date': forms.DateInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500', 'type': 'date'}),
            'is_fixed': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'}),
        }

    def __init__(self, user, *args, **kwargs):
        super(ExpenseForm, self).__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(user=user, category_type='Expense')
# In forms.py, add this class
class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ['category', 'amount_limit', 'start_date', 'end_date']
        widgets = {
            'category': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500'}),
            'amount_limit': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500', 'step': '0.01'}),
            'start_date': forms.DateInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        # Extract user from kwargs
        user = kwargs.pop('user', None)
        
        # If first arg is not a dict (when form data is passed), check if it's the user object
        if args and not isinstance(args[0], (dict, None.__class__)) and not user:
            user = args[0]
            args = args[1:]
        
        super(BudgetForm, self).__init__(*args, **kwargs)
        
        if user:
            self.fields['category'].queryset = Category.objects.filter(user=user, category_type='Expense')
# In forms.py
# forms.py - Modified EMIForm class
class EMIForm(forms.ModelForm):
    class Meta:
        model = EMI
        fields = ['total_amount', 'amount', 'start_date', 'end_date', 
                 'frequency', 'description', 'next_payment_date']
        widgets = {
            'total_amount': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500', 'step': '0.01'}),
            'amount': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500', 'step': '0.01'}),
            'start_date': forms.DateInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500', 'type': 'date'}),
            'frequency': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500', 'rows': 3}),
            'next_payment_date': forms.DateInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500', 'type': 'date'}),
        }

    def __init__(self, user, *args, **kwargs):
        super(EMIForm, self).__init__(*args, **kwargs)
        
        # Set initial value for next_payment_date to start_date by default
        if not self.instance.pk and not self.initial.get('next_payment_date'):
            self.fields['next_payment_date'].initial = self.initial.get('start_date')
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        next_payment_date = cleaned_data.get('next_payment_date')
        end_date = cleaned_data.get('end_date')
        
        # Validate the dates
        if start_date and end_date and start_date > end_date:
            raise ValidationError("Start date cannot be after end date.")
            
        # Ensure next_payment_date is not before start_date
        if start_date and next_payment_date and next_payment_date < start_date:
            raise ValidationError("Next payment date cannot be before start date.")
            
        # Ensure next_payment_date is not after end_date
        if end_date and next_payment_date and next_payment_date > end_date:
            raise ValidationError("Next payment date cannot be after end date.")
            
        return cleaned_data