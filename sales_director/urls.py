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
from .views import SalesPersonDetails , InsertSalesTarget,GetSalesPersonsIdsNames,GetSalesPersonDetails,UpdateSalesPersonProfile,GetSalesCommision,GetDemoRequests,UpdateDemoRequest
#sales_routes in routes.txt
urlpatterns = [
    path('get_all_salespersons_overview/',SalesPersonDetails.as_view(),name="sales_overview"),#/get_all_salespersons_overview
    path('insert_sales_target/',InsertSalesTarget.as_view(),name="insert_sales_target"),#/insert_sales_target
    path('get_salespersons/',GetSalesPersonsIdsNames.as_view(),name="get_salespersons"),#/salespersons_ids
    path('get_salesperson_details/<int:sale_person_id>/',GetSalesPersonDetails.as_view(),name="get_salesperson_details"),#/get_salesperson_details_by_id/<int:sale_person_id>,/get_salesperson_details/<int:sale_person_id>
    path('get_sales_commission/',GetSalesCommision.as_view(),name="get_sales_commision"),#/get_sales_commission
    path('update_profile/<int:sale_person_id>/',UpdateSalesPersonProfile.as_view(),name="update_sales_person_profile"),#/update_comission_percent/<int:sale_person_id>,/update_country/<int:sales_person_id>
    path('demo_request/',GetDemoRequests.as_view(),name="get_demo_requests"),#/demo_requests,
    path('update_demo_request/',UpdateDemoRequest.as_view(),name="update_demo_requests"),#/assign_salesperson,
    path('get_sales_revenue/',UpdateDemoRequest.as_view(),name="update_demo_requests"), #/get_sales_revenue,/get_sales_revenue_by_id/<int:sale_person_id>
]
