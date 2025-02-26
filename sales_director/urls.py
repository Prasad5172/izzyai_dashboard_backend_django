"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path , include
from .views import SalesPersonDetails,SalesPersonsFullDetails,GetSalesPersonsRevenue
#sales_routes in routes.txt
urlpatterns = [
    path('get_all_salespersons_overview/',SalesPersonDetails.as_view(),name="sales_overview"),#/get_all_salespersons_overview
    path('get_salesperson_details/<int:sale_person_id>/',SalesPersonsFullDetails.as_view(),name="get_salesperson_details"),#/get_salesperson_details_by_id/<int:sale_person_id>,/get_salesperson_details/<int:sale_person_id>
    path('get_sales_revenue/',GetSalesPersonsRevenue.as_view(),name="update_demo_requests"), #/get_sales_revenue,/get_sales_revenue_by_id/<int:sale_person_id>
]
