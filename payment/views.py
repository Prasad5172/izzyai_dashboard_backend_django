from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models.functions import ExtractYear
from .models import Payment
from django.db.models import Q,Count,F
from datatime import datetime
from django.db.models import Sum, Value, FloatField, Coalesce, TruncMonth
from authentication.models import CustomUser
from clinic.models import Clinics
from django.shortcuts import get_object_or_404
from .models import Subscriptions,Invoice,Coupon
from authentication.models import CustomUser,UserProfile,UsersInsurance
import uuid
from django.utils import timezone
# Create your views here.
#/get_payment_years
class PaymentYears(APIView):
    def get(self, request):
        try:
            years = (
                Payment.objects
                .filter(payment_date__isnull=False)
                .annotate(year=ExtractYear("payment_date"))
                .values_list("year", flat=True)
                .distinct()
                .order_by("-year")
            )
            return Response({},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error":f'Error occurred: {str(e)}'},status=status.HTTP_400_BAD_REQUEST)

#/get_monthly_revenue
class monthly_revenue(APIView):
    def get(self, request):
        try:
            year = request.GET.get('year', None)
            yearly = request.GET.get('yearly', 'false').lower() == 'true'
            base_filter = Q(payment_status="Paid") & Q(user__user_type__in=["patient", "clinic"])
            if yearly:
                # Yearly revenue query
                yearly_revenue = (
                    Payment.objects
                    .filter(base_filter)
                    .annotate(year=ExtractYear("payment_date"))
                    .values("year")
                    .annotate(total_revenue=Coalesce(Sum("amount"), Value(0.0, output_field=FloatField())))
                    .order_by("year")
                )

                # Convert QuerySet to list
                yearly_revenue_list = list(yearly_revenue)
            else:
                # Default year is the current year if not provided
                if not year:
                    year = datetime.now().year

                # Monthly revenue query
                monthly_revenue = (
                    Payment.objects
                    .filter(base_filter & Q(payment_date__year=year))
                    .annotate(
                        month=TruncMonth("payment_date"),  # Get month from date
                    )
                    .values("month")
                    .annotate(total_revenue=Coalesce(Sum("amount"), Value(0.0, output_field=FloatField())))
                    .order_by("month")
                )

                # Convert QuerySet to list with formatted month names
                monthly_revenue_list = [
                    {
                        "month": row["month"].strftime("%b"),  # Convert to short month name (e.g., "Jan")
                        "total_revenue": row["total_revenue"]
                    }
                    for row in monthly_revenue
                ]

            return Response(monthly_revenue_list,status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error":f'Error occurred: {str(e)}'},status=status.HTTP_400_BAD_REQUEST)

#/get_transaction
class UserTypePayments(APIView):
    def get(self, request):
        try:
            user_type = request.GET.get('user_type', None)
            base_filter = Q(payment_status="Paid") & Q(user__user_type__in=["patient", "clinic"])
            if user_type:
                user_payments = (
                    Payment.objects
                    .filter(base_filter & Q(user__user_type=user_type))
                    .values("user__user_type")
                    .annotate(total_revenue=Coalesce(Sum("amount"), Value(0.0, output_field=FloatField())))
                    .order_by("user__user_type")
                )

                # Convert QuerySet to list
                user_payments_list = list(user_payments)
                return Response(user_payments_list,status=status.HTTP_200_OK)
            else:
                return Response({"error":"user_type is required"},status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error":f'Error occurred: {str(e)}'},status=status.HTTP_400_BAD_REQUEST)
#/create_invoice
#/get_invoices
#/delete_invoice/<int:invoice_id>
#/get_invoice/<int:invoice_id>
class InvoiceView(APIView):
    def post(self, request):
        try:
            user_id = request.GET.get('user_id', None)
            # Extract data from form-data
            customer_name = request.data.get('customer_name')
            customer_email = request.data.get('customer_email')
            subscription_id = request.data.get('subscription_id')
            subscription_count = request.data.get('subscription_count')
            due_date = request.data.get('due_date')
            clinic_id = request.data.get('clinic_id')

            user = get_object_or_404(CustomUser, user_id=user_id)
            clinic = get_object_or_404(Clinics, clinic_id=clinic_id)

            subscription_price = 53
            total_amount = subscription_price * int(subscription_count)
            subscription = get_object_or_404(Subscriptions, subscription_id=subscription_id)

            user_insurance = Invoice.objects.create(
                customer_name = customer_name,
                customer_email = customer_email,
                amount = total_amount,
                subscription = subscription,
                subscription_count = subscription_count,
                issue_date = datetime.now(),
                invoice_status = "Pending",
                due_date = due_date,
                user = user,
                clinic = clinic,
            )
            return Response(user_insurance,status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error":f'Error occurred: {str(e)}'},status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, invoice_id):
        try:
            invoice = get_object_or_404(Invoice, invoice_id=invoice_id)
            invoice.delete()
            return Response({"message":"Invoice deleted successfully"},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error":f'Error occurred: {str(e)}'},status=status.HTTP_400_BAD_REQUEST)

    def get(self, request,invoice_id):
        try:
            invoice = get_object_or_404(Invoice, invoice_id=invoice_id)
            return Response(invoice,status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error":f'Error occurred: {str(e)}'},status=status.HTTP_400_BAD_REQUEST)
    

#/get_subscriptions_ids
#//get_subscriptions
class SubscriptionsView(APIView):
    def get(self, request):
        try:
            subscriptions = Subscriptions.objects.all().values("subscription_id", "subscription_name", "subscription_price")
            return Response(subscriptions,status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error":f'Error occurred: {str(e)}'},status=status.HTTP_400_BAD_REQUEST)

#/get_coupons
#/generate_coupon 
#need to implement coupon email
class CouponsView(APIView):
    def get(self,request):
        try:
            coupons = Coupon.objects.all().values("coupon_id","code","user_id","user_type","discount","free_trial","expiration_date","is_used","redemption_count")
            return Response({coupons},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error":f'Error occurred: {str(e)}'},status=status.HTTP_400_BAD_REQUEST)
    
    def post(self,request):
        try:
            user_id = request.data.get('user_id')
            #user_type = request.data.get('user_type') # i think we don't need to input this we can fetch it from userid
            discount = int(request.data.get('discount', 5))
            free_trial_days = int(request.data.get('free_trial', 0))
            expiration_in_months = int(request.data.get('expiration_in_months',1))
            user = get_object_or_404(CustomUser, id=user_id)
    
            # Get user email
            user_email = user.email
            user_type = user.user_type

            # Get user name based on type
            if user_type == 'patient':
                user_profile = get_object_or_404(UserProfile, user=user)
                user_name = user_profile.full_name
            elif user_type == 'clinic':
                clinic = get_object_or_404(Clinics, user=user)
                user_name = clinic.clinic_name
            else:
                return Response({'error': 'Invalid user type. Must be "Patient" or "Clinic".'}, status=status.HTTP_400_BAD_REQUEST)

            # Validate input
            if discount % 5 != 0 or discount < 5 or discount > 100:
                return Response({'error': 'Invalid discount percentage. Must be in 5% increments from 5% to 100%.'}, status=status.HTTP_400_BAD_REQUEST)

            if free_trial_days not in [0, 7, 30]:
                return Response({'error': 'Free trial must be 0, 7, or 30 days.'}, status=status.HTTP_400_BAD_REQUEST)

            # Generate unique coupon code
            coupon_code = str(uuid.uuid4()).replace('-', '')[:10]

            # Set expiration date
            expiration_date = timezone.now().date()
            if discount == 100:
                if expiration_in_months < 1 or expiration_in_months > 3:
                    return Response({'error': 'Invalid expiration period. Must be between 1 and 3 months for 100% coupons.'}, status=status.HTTP_400_BAD_REQUEST)
                expiration_date += timezone.timedelta(days=30 * expiration_in_months)
            else:
                expiration_date += timezone.timedelta(days=7 if user_type == 'individual' else 30)

            if free_trial_days > 0:
                expiration_date += timezone.timedelta(days=free_trial_days)

            # Create the coupon
            Coupon.objects.create(
                user=user,
                user_type=user_type,
                code=coupon_code,
                discount=discount,
                free_trial=free_trial_days,
                expiration_date=expiration_date
            )
            # Email the coupon (Function should be implemented separately)
            if user_type == 'Patient':
                pass
                #send_individual_coupon_email(user_name, user_email, coupon_code, discount, expiration_date)
            else:
                pass
                #send_clinic_coupon_email(user_name, user_email, coupon_code, discount, expiration_date)

            return Response({
                'CouponCode': coupon_code,
                'UserID': user_id,
                'UserType': user_type,
                'Discount': discount,
                'FreeTrial': free_trial_days,
                'ExpirationDate': expiration_date
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error":f'Error occurred: {str(e)}'},status=status.HTTP_400_BAD_REQUEST)

#/get_transaction_history/<int:user_id>
class UserPaymentsHistoryView(APIView):
    def get(self,request,user_id):
        try:
           transaction_data = Payment.objects.filter(user_id=user_id).values("user_id","payment_id","payment_date","amount","owner_name","payment_status")
           return Response(transaction_data,status=status.HTTP_200_OK)
        except Exception as e:
           return Response({"error":f'Error occurred: {str(e)}'},status=status.HTTP_400_BAD_REQUEST)
#//get_processing_and_claimed_users
class GetProcessingAndClaimedUsers(APIView):
    def post(self,request):
        try:
           query_result = UsersInsurance.objects.aggregate(
               active_clinic_user = Count("insurance_id",filter=Q(insurance_status="Processing")),
               user_using_insurance = Count("insurance_id",filter=Q(insurance_status="Claimed"))
           )
           return Response(query_result,status=status.HTTP_200_OK)
        except Exception as e:
           return Response({"error":f'Error occurred: {str(e)}'},status=status.HTTP_400_BAD_REQUEST)

