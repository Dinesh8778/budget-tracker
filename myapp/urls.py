from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    
    path('categories/', views.category_list, name='category_list'),
    path('categories/add/', views.add_category, name='add_category'),
    path('categories/<int:category_id>/edit/', views.edit_category, name='edit_category'),
    path('categories/<int:category_id>/delete/', views.delete_category, name='delete_category'),
    
    # Income URLs
    path('incomes/', views.income_list, name='income_list'),
    path('incomes/add/', views.add_income, name='add_income'),
    path('incomes/edit/<int:income_id>/', views.edit_income, name='edit_income'),
    path('incomes/delete/<int:income_id>/', views.delete_income, name='delete_income'),
    
    # Expense URLs
path('expenses/', views.expense_list, name='expense_list'),
path('expenses/add/', views.add_expense, name='add_expense'),
path('expenses/edit/<int:expense_id>/', views.edit_expense, name='edit_expense'),
path('expenses/delete/<int:expense_id>/', views.delete_expense, name='delete_expense'),
    # In urls.py, add these paths
    path('budgets/', views.budget_list, name='budget_list'),
    path('budgets/add/', views.add_budget, name='add_budget'),
    path('budgets/edit/<int:budget_id>/', views.edit_budget, name='edit_budget'),
    path('budgets/delete/<int:budget_id>/', views.delete_budget, name='delete_budget'),
    # urls.py - Add these URLs to your urlpatterns



    # Your existing URL patterns...
    
 # urls.py - Update URL patterns to maintain the same URL structure
      path('emi/', views.EMIListView.as_view(), name='emi_list'),
    path('emi/add/', views.EMICreateView.as_view(), name='add_emi'),
    path('emi/<int:pk>/edit/', views.EMIUpdateView.as_view(), name='edit_emi'),
    path('emi/<int:pk>/delete/', views.EMIDeleteView.as_view(), name='delete_emi'),
]

