from django.shortcuts import render
from django.db.models import Count, Sum, F, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from sales_person.models import SalePersons
from clinic.models import Clinics
from authentication.models import CustomUser
from payment.models import Payment

# Create your views here.
#/get_all_salespersons_overview
class SalesPersonDetails(APIView):
    def get_all_salespersons_overview(request):
        """
        Fetches an overview of all salespersons, including clinic count, user count, sales per clinic, and revenue.
        """
        try:
            salespersons = SalePersons.objects.all().values("id", "name", "country")

            result = []

            for sp in salespersons:
                sale_person_id = sp["id"]
                name = sp["name"]
                country = sp["country"]

                # Count active clinics for the salesperson
                active_clinics = Clinics.objects.filter(sale_person_id=sale_person_id).count()

                # Count total users under the salesperson's clinics
                total_users = CustomUser.objects.filter(
                    user_profiles__clinic_id__sale_person_id=sale_person_id
                ).count()

                # Calculate Sales Per Clinic (rounding up)
                sales_per_clinic = total_users // active_clinics if active_clinics > 0 else 0

                # Calculate total revenue generated
                revenue_generated = Payment.objects.filter(
                    user_id__user_profiles__clinic_id__sale_person_id=sale_person_id
                ).aggregate(total_revenue=Sum("amount"))["total_revenue"] or 0

                result.append({
                    "SalePersonID": sale_person_id,
                    "Name": name,
                    "Country": country,
                    "ActiveClinics": active_clinics,
                    "SalesPerClinic": sales_per_clinic,
                    "RevenueGenerated": revenue_generated
                })
            return Response({result:result},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
