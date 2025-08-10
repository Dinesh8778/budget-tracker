from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
import json
from decimal import Decimal
from django.db import models
from datetime import date
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.template.loader import render_to_string
from .forms import UserCreationForm, CategoryForm, IncomeForm, ExpenseForm, BudgetForm, EMIForm
from .models import Income, Expense, Category, Budget, EMI, User
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.template.loader import render_to_string
from decimal import Decimal
from django.db import models

from .models import Budget, Expense
from .forms import BudgetForm
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})
@login_required
def dashboard(request):
    # Get current date
    current_date = timezone.now().date()
    
    # Check if specific date filter is provided
    specific_date = request.GET.get('specific_date')
    
    # Get filter parameters
    filter_month = int(request.GET.get('month', current_date.month))
    filter_year = int(request.GET.get('year', current_date.year))
    
    # Process due EMI payments
    process_due_emi_payments(request)
    
    # Get all years with transactions for the filter dropdown
    income_years = set(Income.objects.filter(user=request.user).dates('date', 'year').values_list('date__year', flat=True))
    expense_years = set(Expense.objects.filter(user=request.user).dates('date', 'year').values_list('date__year', flat=True))
    available_years = sorted(list(income_years.union(expense_years)))
    
    if not available_years:
        available_years = [current_date.year]
    
    # Initialize filtered data queries
    if specific_date:
        # Convert specific_date string to date object
        try:
            specific_date_obj = datetime.strptime(specific_date, '%Y-%m-%d').date()
            filtered_income_data = Income.objects.filter(
                user=request.user,
                date=specific_date_obj
            )
            filtered_expense_data = Expense.objects.filter(
                user=request.user,
                date=specific_date_obj
            )
            
            # For specific date, we'll use a single-day range for the chart
            month_start = specific_date_obj
            month_end = specific_date_obj
        except ValueError:
            # If date format is invalid, fall back to month/year filter
            filtered_income_data = Income.objects.filter(
                user=request.user,
                date__month=filter_month,
                date__year=filter_year
            )
            filtered_expense_data = Expense.objects.filter(
                user=request.user,
                date__month=filter_month,
                date__year=filter_year
            )
            
            # Set up month range for daily data chart
            month_start = datetime(filter_year, filter_month, 1).date()
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    else:
        # Use month/year filter (default)
        filtered_income_data = Income.objects.filter(
            user=request.user,
            date__month=filter_month,
            date__year=filter_year
        )
        filtered_expense_data = Expense.objects.filter(
            user=request.user,
            date__month=filter_month,
            date__year=filter_year
        )
        
        # Set up month range for daily data chart
        month_start = datetime(filter_year, filter_month, 1).date()
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    # Calculate totals
    filtered_income = filtered_income_data.aggregate(total=Sum('amount'))['total'] or 0
    filtered_expense = filtered_expense_data.aggregate(total=Sum('amount'))['total'] or 0
    filtered_savings = filtered_income - filtered_expense
    
    # Get daily data for line chart
    daily_data = []
    
    for day in range((month_end - month_start).days + 1):
        current_date = month_start + timedelta(days=day)
        daily_income = Income.objects.filter(
            user=request.user,
            date=current_date
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        daily_expense = Expense.objects.filter(
            user=request.user,
            date=current_date
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        daily_data.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'income': float(daily_income),
            'expense': float(daily_expense)
        })
    
    # Get monthly data for bar chart (last 6 months)
    current_date = timezone.now().date()  # Reset current_date after using it in the loop
    months_labels = []
    monthly_income = []
    monthly_expenses = []
    monthly_savings = []
    
    for i in range(5, -1, -1):
        month_date = current_date.replace(day=1) - timedelta(days=1*i*30)
        month_name = month_date.strftime('%b %Y')
        months_labels.append(month_name)
        
        month_income = Income.objects.filter(
            user=request.user,
            date__month=month_date.month,
            date__year=month_date.year
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        month_expense = Expense.objects.filter(
            user=request.user,
            date__month=month_date.month,
            date__year=month_date.year
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        month_savings = month_income - month_expense
        
        monthly_income.append(float(month_income))
        monthly_expenses.append(float(month_expense))
        monthly_savings.append(float(month_savings))
    
    # Get income by category data
    income_by_category = filtered_income_data.values('category__name').annotate(total=Sum('amount'))
    income_category_labels = [item['category__name'] for item in income_by_category]
    income_category_data = [float(item['total']) for item in income_by_category]
    
    # Get expenses by category data
    expense_by_category = filtered_expense_data.values('category__name').annotate(total=Sum('amount'))
    expense_category_labels = [item['category__name'] for item in expense_by_category]
    expense_category_data = [float(item['total']) for item in expense_by_category]
    
    context = {
        'total_income': request.user.total_income(),
        'total_expense': request.user.total_expense(),
        'total_savings': request.user.total_savings(),
        'filtered_income': filtered_income,
        'filtered_expense': filtered_expense,
        'filtered_savings': filtered_savings,
        'current_month': filter_month,
        'current_year': filter_year,
        'available_years': available_years,
        'specific_date': specific_date,
        'months_labels': json.dumps(months_labels),
        'monthly_income': json.dumps(monthly_income),
        'monthly_expenses': json.dumps(monthly_expenses),
        'monthly_savings': json.dumps(monthly_savings),
        'income_category_labels': json.dumps(income_category_labels),
        'income_category_data': json.dumps(income_category_data),
        'expense_category_labels': json.dumps(expense_category_labels),
        'expense_category_data': json.dumps(expense_category_data),
        'daily_data': json.dumps(daily_data)
    }
    
    return render(request, 'dashboard.html', context)

def process_due_emi_payments(request):
    """Process all due EMI payments and create corresponding expense entries"""
    today = timezone.now().date()
    due_emis = EMI.objects.filter(
        user=request.user,
        is_active=True,
        next_payment_date__lte=today
    )
    
    processed_count = 0
    for emi in due_emis:
        # Create expense entry for this payment
        expense = emi.create_expense()
        
        # Update the next payment date
        emi.update_next_payment_date()
        
        processed_count += 1
        
        # Add a message for each processed EMI
        messages.info(
            request, 
            f'EMI payment of ₹{emi.amount} for {emi.description} has been processed.'
        )
    
    return processed_count

# Category views
@login_required
def category_list(request):
    categories = Category.objects.filter(user=request.user).order_by('category_type', 'name')
    return render(request, 'categories/category_list.html', {'categories': categories})
@login_required
def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user
            category.save()
            messages.success(request, 'Category added successfully!')
            
            # If AJAX request, return JSON response
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Category added successfully!'
                })
            
            return redirect('category_list')
    else:
        form = CategoryForm()
        
    # If AJAX request and form is invalid, return errors
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.method == 'POST':
        return JsonResponse({
            'success': False,
            'message': 'Please correct the errors below.',
            'errors': dict(form.errors.items())
        })
        
    return render(request, 'categories/category_form.html', {'form': form, 'title': 'Add Category'})

@login_required
def edit_category(request, category_id):
    category = get_object_or_404(Category, id=category_id, user=request.user)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully!')
            
            # If AJAX request, return JSON response
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Category updated successfully!'
                })
                
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category)
    
    # If AJAX request and form is invalid, return errors
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.method == 'POST':
        return JsonResponse({
            'success': False,
            'message': 'Please correct the errors below.',
            'errors': dict(form.errors.items())
        })
        
    return render(request, 'categories/category_form.html', {'form': form, 'title': 'Edit Category'})

@login_required
def delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id, user=request.user)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted successfully!')
        
        # If AJAX request, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Category deleted successfully!'
            })
            
        return redirect('category_list')
        
    return render(request, 'categories/category_confirm_delete.html', {'category': category})

# Income views
@login_required
def income_list(request):
    # Get filter parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    is_filtered = bool(start_date and end_date)
    
    # Base query
    income_query = Income.objects.filter(user=request.user)
    
    # Apply date filtering if provided
    if is_filtered:
        income_query = income_query.filter(date__gte=start_date, date__lte=end_date)
    
    # Get results and calculate total
    incomes = income_query.order_by('-date')
    total = income_query.aggregate(Sum('amount'))['amount__sum'] or 0
    
    return render(request, 'incomes/income_list.html', {
        'incomes': incomes, 
        'total': total,
        'start_date': start_date,
        'end_date': end_date,
        'is_filtered': is_filtered
    })

@login_required
def add_income(request):
    if request.method == 'POST':
        form = IncomeForm(request.user, request.POST)
        if form.is_valid():
            income = form.save(commit=False)
            income.user = request.user
            income.save()
            messages.success(request, 'Income added successfully!')
            
            # If it's an AJAX request, return JSON response
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            
            return redirect('income_list')
    else:
        form = IncomeForm(request.user)
    
    # If it's an AJAX request and GET method, return only the form
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.method == 'GET':
        return render(request, 'incomes/income_form.html', {'form': form, 'title': 'Add Income'})
    
    return render(request, 'incomes/income_form.html', {'form': form, 'title': 'Add Income'})

@login_required
def edit_income(request, income_id):
    income = get_object_or_404(Income, id=income_id, user=request.user)
    if request.method == 'POST':
        form = IncomeForm(request.user, request.POST, instance=income)
        if form.is_valid():
            form.save()
            messages.success(request, 'Income updated successfully!')
            
            # If it's an AJAX request, return JSON response
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            
            return redirect('income_list')
    else:
        form = IncomeForm(request.user, instance=income)
    
    # If it's an AJAX request and GET method, return only the form
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.method == 'GET':
        return render(request, 'incomes/income_form.html', {'form': form, 'title': 'Edit Income'})
    
    return render(request, 'incomes/income_form.html', {'form': form, 'title': 'Edit Income'})

@login_required
def delete_income(request, income_id):
    income = get_object_or_404(Income, id=income_id, user=request.user)
    if request.method == 'POST':
        income.delete()
        messages.success(request, 'Income deleted successfully!')
        
        # If it's an AJAX request, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        
        return redirect('income_list')
    
    # If it's an AJAX request and GET method, return only the confirmation
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.method == 'GET':
        return render(request, 'incomes/income_confirm_delete.html', {'income': income})
    
    return render(request, 'incomes/income_confirm_delete.html', {'income': income})
# Expense views
@login_required
def expense_list(request):
    # Get filter parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    is_filtered = bool(start_date and end_date)
    
    # Base query
    expense_query = Expense.objects.filter(user=request.user)
    
    # Apply date filtering if provided
    if is_filtered:
        expense_query = expense_query.filter(date__gte=start_date, date__lte=end_date)
    
    # Get results and calculate total
    expenses = expense_query.order_by('-date')
    total = expense_query.aggregate(Sum('amount'))['amount__sum'] or 0
    
    return render(request, 'expenses/expense_list.html', {
        'expenses': expenses, 
        'total': total,
        'start_date': start_date,
        'end_date': end_date,
        'is_filtered': is_filtered
    })

@login_required
def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.user, request.POST)
        if form.is_valid():
            # Don't save immediately
            expense = form.save(commit=False)
            expense.user = request.user
            
            # Check if form submission includes a confirmation to override budget
            budget_override = request.POST.get('budget_override') == 'true'
            
            # Check budget limits
            budget_alert = check_budget_alert(request, expense)
            
            # If exceeding budget and not confirmed, return to form with alert
            if budget_alert and budget_alert['severity'] == 'exceeded' and not budget_override:
                # If AJAX request, return JSON with budget alert
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    html_response = render_to_string('expenses/expense_form.html', {
                        'form': form, 
                        'expense': expense,
                        'budget_alert': budget_alert
                    }, request=request)
                    
                    return JsonResponse({
                        'success': False,
                        'budget_alert': budget_alert,
                        'html': html_response
                    })
                
                # Pass the alert info to template
                return render(request, 'expenses/expense_form.html', {
                    'form': form, 
                    'expense': expense,
                    'budget_alert': budget_alert
                })
            
            # Save expense if either budget is not exceeded or user confirmed override
            expense.save()
            
            # Show appropriate message
            message = 'Expense added successfully!'
            if budget_alert and budget_alert['severity'] == 'exceeded' and budget_override:
                message = f'Expense added despite exceeding your budget for {budget_alert["category"]} by ₹{budget_alert["overspend_amount"]:.2f}.'
            elif budget_alert and budget_alert['severity'] == 'approaching':
                message = f'Warning: You are approaching your budget limit for {budget_alert["category"]}. ₹{budget_alert["remaining"]:.2f} remaining.'
            
            messages.success(request, message)
            
            # If AJAX request, return JSON response
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': message
                })
                
            return redirect('expense_list')
    else:
        form = ExpenseForm(request.user)
    
    # If AJAX request, return form HTML
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'expenses/expense_form.html', {
            'form': form
        })
    
    return render(request, 'expenses/expense_form.html', {'form': form})
@login_required
def edit_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id, user=request.user)
    if request.method == 'POST':
        form = ExpenseForm(request.user, request.POST, instance=expense)
        if form.is_valid():
            # Don't save immediately
            expense = form.save(commit=False)
            
            # Check if form submission includes a confirmation to override budget
            budget_override = request.POST.get('budget_override') == 'true'
            
            # Check budget limits
            budget_alert = check_budget_alert(request, expense)
            
            # If exceeding budget and not confirmed, return to form with alert
            if budget_alert and budget_alert['severity'] == 'exceeded' and not budget_override:
                # If AJAX request, return JSON with budget alert
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    html_response = render_to_string('expenses/expense_form.html', {
                        'form': form, 
                        'expense': expense,
                        'budget_alert': budget_alert
                    }, request=request)
                    
                    return JsonResponse({
                        'success': False,
                        'budget_alert': budget_alert,
                        'html': html_response
                    })
                
                # Pass the alert info to template
                return render(request, 'expenses/expense_form.html', {
                    'form': form, 
                    'expense': expense,
                    'budget_alert': budget_alert
                })
            
            # Save expense if either budget is not exceeded or user confirmed override
            expense.save()
            
            # Show appropriate message
            message = 'Expense updated successfully!'
            if budget_alert and budget_alert['severity'] == 'exceeded' and budget_override:
                message = f'Expense updated despite exceeding your budget for {budget_alert["category"]} by ₹{budget_alert["overspend_amount"]:.2f}.'
            elif budget_alert and budget_alert['severity'] == 'approaching':
                message = f'Warning: You are approaching your budget limit for {budget_alert["category"]}. ₹{budget_alert["remaining"]:.2f} remaining.'
            
            messages.success(request, message)
            
            # If AJAX request, return JSON response
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': message
                })
                
            return redirect('expense_list')
    else:
        form = ExpenseForm(request.user, instance=expense)
    
    # If AJAX request, return form HTML
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'expenses/expense_form.html', {
            'form': form,
            'expense': expense
        })
    
    return render(request, 'expenses/expense_form.html', {'form': form, 'expense': expense})

@login_required
def delete_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id, user=request.user)
    if request.method == 'POST':
        expense.delete()
        messages.success(request, 'Expense deleted successfully!')
        
        # If AJAX request, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Expense deleted successfully!'
            })
        
        return redirect('expense_list')
    
    # If AJAX request, return confirmation HTML
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'expenses/expense_confirm_delete.html', {
            'expense': expense,
            'is_popup': True
        })
    
    return render(request, 'expenses/expense_confirm_delete.html', {'expense': expense})


## Budget views
@login_required
def budget_list(request):
    budgets = Budget.objects.filter(user=request.user).order_by('category__name')
    
    # Clear any Django messages if we're redirected with the no_messages flag
    # This prevents duplicate notifications when using both AJAX and Django messaging
    if request.GET.get('no_messages') == '1':
        storage = messages.get_messages(request)
        for message in storage:
            pass  # Just iterating clears the messages
    
    return render(request, 'budgets/budget_list.html', {'budgets': budgets})

@login_required
def add_budget(request):
    if request.method == 'POST':
        # Only process AJAX requests to prevent double submission
        if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'Invalid request method'
            })
            
        form = BudgetForm(data=request.POST, user=request.user)
        if form.is_valid():
            category = form.cleaned_data['category']
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            
            # Check for existing budget for this category and date range
            existing_budget = Budget.objects.filter(
                user=request.user,
                category=category,
                start_date=start_date,
                end_date=end_date
            ).exists()
            
            if existing_budget:
                # Budget already exists for this category and date range
                return JsonResponse({
                    'success': False,
                    'message': f'A budget limit for {category.name} already exists for this date range.'
                })
            else:
                # Create new budget
                budget = form.save(commit=False)
                budget.user = request.user
                budget.save()
                
                # Add message to Django messages but don't show it
                # The AJAX response will handle the notification
                # This is for non-JS fallback only
                messages.success(request, 'Budget limit added successfully!')
                
                return JsonResponse({
                    'success': True, 
                    'message': 'Budget limit added successfully!'
                })
        else:
            # Handle form errors
            form_html = render_to_string('budgets/partials/budget_form_fields.html', 
                                      {'form': form}, request=request)
            return JsonResponse({
                'success': False, 
                'form_html': form_html
            })
    else:
        form = BudgetForm(user=request.user)
        
        # Return just the form fields for AJAX requests
        if request.GET.get('ajax') == 'true':
            form_html = render_to_string('budgets/partials/budget_form_fields.html', 
                                      {'form': form}, request=request)
            return HttpResponse(form_html)
            
    return render(request, 'budgets/budget_form.html', {'form': form, 'title': 'Add Budget Limit'})

@login_required
def edit_budget(request, budget_id):
    budget = get_object_or_404(Budget, id=budget_id, user=request.user)
    
    if request.method == 'POST':
        # Only process AJAX requests to prevent double submission
        if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'Invalid request method'
            })
            
        form = BudgetForm(data=request.POST, user=request.user, instance=budget)
        if form.is_valid():
            category = form.cleaned_data['category']
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            
            # Check for existing budget for this category and date range (excluding this one)
            existing_budget = Budget.objects.filter(
                user=request.user,
                category=category,
                start_date=start_date,
                end_date=end_date
            ).exclude(id=budget_id).exists()
            
            if existing_budget:
                # Budget already exists for this category and date range
                return JsonResponse({
                    'success': False,
                    'message': f'Another budget limit for {category.name} already exists for this date range.'
                })
            else:
                # Save the budget
                form.save()
                
                # Add message to Django messages but don't show it
                # The AJAX response will handle the notification
                # This is for non-JS fallback only
                messages.success(request, 'Budget limit updated successfully!')
                
                return JsonResponse({
                    'success': True,
                    'message': 'Budget limit updated successfully!'
                })
        else:
            # Handle form errors
            form_html = render_to_string('budgets/partials/budget_form_fields.html', 
                                      {'form': form}, request=request)
            return JsonResponse({
                'success': False, 
                'form_html': form_html
            })
    else:
        form = BudgetForm(user=request.user, instance=budget)
        
        # Return just the form fields for AJAX requests
        if request.GET.get('ajax') == 'true':
            form_html = render_to_string('budgets/partials/budget_form_fields.html', 
                                      {'form': form}, request=request)
            return HttpResponse(form_html)
            
    return render(request, 'budgets/budget_form.html', {'form': form, 'title': 'Edit Budget Limit'})

@login_required
def delete_budget(request, budget_id):
    budget = get_object_or_404(Budget, id=budget_id, user=request.user)
    
    if request.method == 'POST':
        # Only process AJAX requests to prevent double submission
        if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'Invalid request method'
            })
            
        budget.delete()
        
        # Add message to Django messages but don't show it
        # The AJAX response will handle the notification
        # This is for non-JS fallback only
        messages.success(request, 'Budget limit deleted successfully!')
        
        return JsonResponse({
            'success': True, 
            'message': 'Budget limit deleted successfully!'
        })
        
    # For GET requests, still show the confirmation page for non-JS fallback
    return render(request, 'budgets/budget_confirm_delete.html', {'budget': budget})
def check_budget_alert(request, expense):
    """
    Check if an expense exceeds any budget limits
    Args:
        request: The HTTP request object
        expense: The Expense model instance
    Returns:
        Dictionary with budget alert information or None
    """
    # Get all active budgets for this category and user
    active_budgets = Budget.objects.filter(
        user=request.user,
        category=expense.category,
        start_date__lte=expense.date,
        end_date__gte=expense.date
    )
    
    for budget in active_budgets:
        # Calculate total expenses in this budget period
        total_expenses = Expense.objects.filter(
            user=request.user,
            category=expense.category,
            date__range=[budget.start_date, budget.end_date]
        ).exclude(id=expense.id if expense.id else None).aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
        
        # Add the current expense amount to the total
        total_expenses += expense.amount
        
        # If total expenses exceed budget limit
        if total_expenses > budget.amount_limit:
            return {
                'exceeded': True,
                'category': budget.category.name,
                'overspend_amount': total_expenses - budget.amount_limit,
                'budget_limit': budget.amount_limit,
                'severity': 'exceeded'
            }
        # If within 90% of budget limit
        elif total_expenses >= (budget.amount_limit * Decimal('0.9')):
            return {
                'exceeded': False,
                'category': budget.category.name,
                'remaining': budget.amount_limit - total_expenses,
                'budget_limit': budget.amount_limit,
                'severity': 'approaching'
            }
    
    return None
# EMI Class-Based Views 
# In views.py
class EMIListView(LoginRequiredMixin, ListView):
    model = EMI
    template_name = 'emi/emi_list.html'
    context_object_name = 'emis'
    
    def get_queryset(self):
        queryset = EMI.objects.filter(user=self.request.user).order_by('-start_date')
        
        # Calculate progress for each EMI
        for emi in queryset:
            # Calculate total payments made
            total_payments = Expense.objects.filter(
                user=self.request.user,
                description__startswith=f"EMI Payment #{emi.id} - ",
                date__range=[emi.start_date, timezone.now().date()]
            ).count()
            
            # Calculate total expected payments based on frequency
            if emi.frequency == 'Daily':
                days = (emi.end_date - emi.start_date).days + 1
                total_expected = days
            elif emi.frequency == 'Weekly':
                days = (emi.end_date - emi.start_date).days + 1
                total_expected = (days // 7) + (1 if days % 7 > 0 else 0)
            elif emi.frequency == 'Monthly':
                total_months = ((emi.end_date.year - emi.start_date.year) * 12 + 
                                emi.end_date.month - emi.start_date.month) + 1
                total_expected = total_months
            elif emi.frequency == 'Quarterly':
                total_months = ((emi.end_date.year - emi.start_date.year) * 12 + 
                                emi.end_date.month - emi.start_date.month) + 1
                total_expected = (total_months // 3) + (1 if total_months % 3 > 0 else 0)
            elif emi.frequency == 'Semi-Annual':
                total_months = ((emi.end_date.year - emi.start_date.year) * 12 + 
                                emi.end_date.month - emi.start_date.month) + 1
                total_expected = (total_months // 6) + (1 if total_months % 6 > 0 else 0)
            else:  # Annual
                total_months = ((emi.end_date.year - emi.start_date.year) * 12 + 
                                emi.end_date.month - emi.start_date.month) + 1
                total_expected = (total_months // 12) + (1 if total_months % 12 > 0 else 0)
            
            # Calculate progress percentage
            emi.progress = round((total_payments / total_expected) * 100, 2) if total_expected > 0 else 0
            emi.payments_made = total_payments
            emi.total_payments = total_expected
            
            # Calculate remaining amount
            emi.remaining_amount = emi.get_remaining_amount()
        
        return queryset

# In views.py
# views.py - Updated EMICreateView
class EMICreateView(LoginRequiredMixin, CreateView):
    model = EMI
    form_class = EMIForm
    template_name = 'emi/emi_form.html'
    success_url = reverse_lazy('emi_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        
        # Only set next_payment_date to start_date if not explicitly provided
        if not form.instance.next_payment_date:
            form.instance.next_payment_date = form.instance.start_date
        
        response = super().form_valid(form)
        
        # Get or create EMI category after saving
        self.object.get_or_create_emi_category()
            
        messages.success(self.request, 'EMI added successfully!')
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add EMI'
        return context
# Add these class-based views to your views.py file

class EMIUpdateView(LoginRequiredMixin, UpdateView):
    model = EMI
    form_class = EMIForm
    template_name = 'emi/emi_form.html'
    success_url = reverse_lazy('emi_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_queryset(self):
        # Ensure users can only edit their own EMIs
        return EMI.objects.filter(user=self.request.user)
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        
        # Only set next_payment_date to start_date if not explicitly provided
        if not form.instance.next_payment_date:
            form.instance.next_payment_date = form.instance.start_date
        
        response = super().form_valid(form)
        
        # Get or create EMI category after saving
        self.object.get_or_create_emi_category()
        
        # The EMI now has an ID, so we can create an initial expense if needed
        if self.object.next_payment_date <= timezone.now().date():
            self.object.create_expense()
            
        messages.success(self.request, 'EMI added successfully!')
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit EMI'
        return context

class EMIDeleteView(LoginRequiredMixin, DeleteView):
    model = EMI
    template_name = 'emi/emi_confirm_delete.html'
    success_url = reverse_lazy('emi_list')
    
    def get_queryset(self):
        # Ensure users can only delete their own EMIs
        return EMI.objects.filter(user=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(self.request, 'EMI deleted successfully!')
        return response