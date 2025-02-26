from datetime import timedelta,datetime


def create_users(n):
    fake: Faker = Faker()
    users = []
    for i in range(n):
        if i < 10:
            usertype = "sale_person"
        elif i < 20:
            usertype = "sales_director"
        elif i < 50:
            usertype = "patient"
        elif i < 70:
            usertype = "clinic"
        elif i < 90:
            usertype = "slp"
        else:
            usertype = "sales"
        user = CustomUser.objects.create(
            username=fake.user_name()+str(i),
            email=fake.email(),
            password=fake.password(),
            user_type=usertype,
            verified=fake.boolean(),
        )
        users.append(user)
    print(users)
    return users
def create_subscriptions():
    fake:Faker = Faker()
    subscriptions = []
    monthly = Subscriptions.objects.create(
        subscription_id = 1,
        subscription_price = 152,
        subscription_name = "Monthly",
    )
    annual = Subscriptions.objects.create(
        subscription_id = 2,
        subscription_price = 888,
        subscription_name = "Annual",
    )
    subscriptions.append(monthly)
    subscriptions.append(annual)
    return subscriptions

def create_disorders():
    fake: Faker = Faker()
    disorders = []
    disorder_name = ["Articulation","Stammering","Voice","Expressive Language","Receptive Language"]
    for i in range(5):
        disorder = Disorders.objects.create(
            disorder_name=disorder_name[i],
        )
        disorders.append(disorder)
    return disorders

def create_profiles(users):
    fake: Faker = Faker()
    profiles = []
    for user in users:
        profile =UserProfile.objects.create(
            user=user,
            full_name=fake.name(),
            gender=random.choice(["Male", "Female", "Other"]),
            country=fake.country(),
            state=fake.state(),
            status=random.choice(["Active","Inactive", "Archived"]), #Archived means session is completed with slp
            patient_status=random.choice(["New", "Completed"]),
            age=random.randint(6, 80),
        )
        profiles.append(profile)
    return profiles

def create_user_files(users):
    fake: Faker = Faker()
    user_files = []
    for i in range(100):
        user_file = UserFiles.objects.create(
            role=random.choice(["admin", "slp", "sale_person","clinic","sales_director" , "patient"]),
            file_path=fake.file_path(),
            user=users[i],
            file_name=fake.file_name(),
        )
        user_files.append(user_file)
    return user_files

def create_session_type():
    
    session_types = []
    session_type = SessionType.objects.create(
        type_name = "Assessment",
    )
    session_types.append(session_type)
    session_types.append(SessionType.objects.create(
        type_name = "Exercise",
    ))
    return session_types

def create_sessions(users, disorders,session_types):
    fake: Faker = Faker()
    sessions = []
    for i in range(100):
        date = fake.date_time_this_year()
        session = Sessions.objects.create(
            session_status=random.choice(["Completed", "quick_assessment_status"]),
            user=random.choice(users),
            session_type=random.choice(session_types),
            start_time=date,
            end_time=date+timedelta(days=1),
            disorder=random.choice(disorders),
        )
        sessions.append(session)
    return sessions

def create_user_excerise(n,sessions,disorders,users):
    fake: Faker = Faker()
    user_exercises = []
    for i in range(n):
        user_exercise = UserExercises.objects.create(
            total_questions=random.randint(1, 100),
            level_name=fake.name(),
            world_id=random.randint(1, 100),
            sound_id=random.randint(1, 100),
            session=random.choice(sessions),
            sound_id_list=fake.text(),
            disorder=random.choice(disorders),
            user=random.choice(users),
            completion_status=random.choice(["Completed", "Incomplete"]),
            exercise_date=fake.date_time_this_year(),
            score=random.randint(0, 100),
            emotion=random.choice(["Happy", "Sad", "Angry"]),
            completed_questions=random.randint(1, 100),
        )
        user_exercises.append(user_exercise)
    return user_exercises

def create_sale_persons(users,subscriptions):
    fake: Faker = Faker()
    sale_persons = []
    for i in range(10):
        sale_person = SalePersons.objects.create(
            phone=random.randint(1000000000, 9999999999),
            state=fake.state(),
            country=fake.country(),
            status=random.choice(["Active", "Inactive"]),
            user=users[i],
            subscription=random.choice(subscriptions),
            subscription_count=random.randint(1, 10),
            commission_percent=random.randint(1, 10),
        )
        sale_persons.append(sale_person)
    return sale_persons

def create_users_insurance(n,users):
    fake: Faker = Faker()
    user_insurances = []
    for i in range(n):
        user_insurance = UsersInsurance.objects.create(
            cpt_number=random.randint(10000,10000000),
            user=random.choice(users),
            insurance_provider = fake.name(),
            insurance_status = random.choice(["Submitting", "Processing", "Approved", "Declined"]),
            policy_number = random.randint(100000, 999999),
            claim_date = fake.date_this_year(),
        )
        user_insurances.append(user_insurance)
    return user_insurances

def create_sales_targets(n,sale_persons):
    fake: Faker = Faker()
    sales_targets = []
    for i in range(n):
        sales_target = SalesTarget.objects.create(
            sale_person=random.choice(sale_persons),
            month=random.randint(1, 12),
            year=random.randint(2010, 2020),
            target=random.randint(1000, 9999),
        )
        sales_targets.append(sales_target)
    return sales_targets
def create_sale_person_activity_logs(n,sale_persons):
    fake: Faker = Faker()
    sale_person_activity_logs = []
    for i in range(n):
        sale_person_activity_log = SalePersonActivityLog.objects.create(
            sale_person=random.choice(sale_persons),
            meetings=random.randint(1, 10),
            qualifying_calls=random.randint(1, 10),
            renewal_calls=random.randint(1, 10),
            proposals_sent=random.randint(1, 10),
            date=fake.date_time_this_year(),
        )
        sale_person_activity_logs.append(sale_person_activity_log)
    return sale_person_activity_logs

def create_sale_person_pipelines(sale_persons):
    fake: Faker = Faker()
    sale_person_pipelines = []
    for i in range(10):
        sale_person_pipeline = SalePersonPipeline.objects.create(
            sale_person=random.choice(sale_persons),
            qualified_sales=random.randint(1, 10),
            renewals=random.randint(1, 10),
            prospective_sales=random.randint(1, 10),
            closed_sales=random.randint(1, 10),
            date=fake.date_time_this_year(),
        )
        sale_person_pipelines.append(sale_person_pipeline)
    return sale_person_pipelines

def create_sales_directors(users):
    fake: Faker = Faker()
    sales_directors = []
    for i in range(10,20):
        sales_director = SalesDirector.objects.create(
            user=users[i],
            department=random.choice(["sales"]),
            designation=random.choice(["Head","director","regional director"]),
        )
        sales_directors.append(sales_director)
    return sales_directors

def create_patient_files(users,start,end):
    fake: Faker = Faker()
    patient_files = []
    for i in range(start,end):
        patient_file = PatientFiles.objects.create(
            file_name=fake.file_name(),
            document_type = fake.uri_extension(),
            diagnosis_name = fake.name(),
            role=random.choice(["Patient", "SLP"]),
            file_path=fake.file_path(),
            user=users[i],
            upload_timestamp=fake.date_time_this_year(),
        )
        patient_files.append(patient_file)
    return patient_files

def create_assessment_results(users,sessions,disorders,n):
    fake: Faker = Faker()
    assessment_results = []
    for i in range(n):
        assessment_result = AssessmentResults.objects.create(
            user = users[i%30+20],
            session=random.choice(sessions),
            score = random.randint(0, 100),
            disorder=random.choice(disorders),
            sound_id_list = fake.text(),
            word_id_list = fake.text(),
            emotion = random.choice(["Happy", "Sad", "Angry"]),
            assessment_date = fake.date_time_this_year(),
            quick_assessment = random.choice(["Completed", "Incomplete"]),
        )
        assessment_results.append(assessment_result)
    return assessment_results   

def create_clinics(n,users,sale_persons):
    fake: Faker = Faker()
    clinics = []
    for i in range(n):
        clinic = Clinics.objects.create(
            izzyai_patients=random.randint(100, 150),
            state=fake.state(),
            total_patients=random.randint(100, 150),
            slp_count = random.randint(1, 10),
            sale_person = random.choice(sale_persons),
            country=fake.country(),
            user = users[i+50],
            email=fake.email(),
            ein_number=random.randint(100000, 999999),
            phone=random.randint(1000000000, 9999999999),
            clinic_name=fake.company(),
            address=fake.address(),
        )
        clinics.append(clinic)
    return clinics
def create_demo_requests(n,sale_persons):
    fake: Faker = Faker()
    demo_requests = []
    for i in range(n):
        demo_request = DemoRequested.objects.create(
            clinic_name=fake.company(),
            first_name=fake.name(),
            last_name=fake.name(),
            country=fake.country(),
            comments=fake.text(),
            contact_number=random.randint(1000000000, 9999999999),
            sales_person=sale_persons[i%10],
            email=fake.email(),
            patients_count  = random.randint(1, 100),
        )
        demo_requests.append(demo_request)
    return demo_requests

def create_slps(n,users,clinics):
    fake: Faker = Faker()
    slps = []
    for i in range(n):
        slp = Slps.objects.create(
            profile_image_path=fake.image_url(),
            status=random.choice(["Active", "Inactive"]),
            country=fake.country(),
            state=fake.state(),
            email=fake.email(),
            slp_name=fake.name(),
            user=users[80+i],
            clinic=clinics[i%10],
            phone=random.randint(1000000000, 9999999999),
        )
        slps.append(slp)
    return slps

def create_slp_appoinments(n,users,slps,disorders):
    fake: Faker = Faker()
    slp_appoinments = []
    for i in range(n):
        slp_appointment = SlpAppointments.objects.create(
            disorder = random.choice(disorders),
            slp=random.choice(slps),
            user=users[20+i],
            appointment_date=fake.date_this_year(),
            session_type=random.choice(["Assessment", "Treatment"]),
            appointment_status = random.choice(["Attended", "Canceled","Pending"]),
            start_time=fake.date_time_this_year(),
            end_time=fake.date_time_this_year(),
        )
        slp_appoinments.append(slp_appointment)
    return slp_appoinments

def create_sales(n,clinics):
    sales = []
    for i in range(n):
        clinic = clinics[i%20]
        sale = Sales.objects.create(
            sale_person=clinic.sale_person,
            subscription_count=random.randint(1, 10),
            commission_percent=random.randint(1, 50),
            clinic=clinic,
            payment_status=random.choice(["Paid", "Unpaid"]),
            subscription_type=random.choice(["Monthly", "Yearly"]),
        )
        sales.append(sale)
    return sales

def create_clinic_appointments(n,users,clinics,slps,disorders):
    fake: Faker = Faker()
    clinic_appointments = []
    for i in range(n):
        date_str =fake.date()
        time_str = fake.time()
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()  # Convert to date object
        time_obj = datetime.strptime(time_str, "%H:%M:%S").time()
        clinic = clinics[i%10]
        slp = slps[i%10]
        clinic_appointment = ClinicAppointments.objects.create(
            clinic=clinic,
            slp = slp,#this should be clinic slps
            session_type=random.choice(["Assessment", "Exercise","Language Therapy"]),
            appointment_status = random.choice(["Attended", "Canceled","Pending"]),
            appointment_date = date_str,
            appointment_start = time_str,
            appointment_end = (datetime.combine(date_obj, time_obj) + timedelta(hours=1)).time(),
            disorder = random.choice(disorders),
            user = users[i%30+20],
        )
        clinic_appointments.append(clinic_appointment)
    return clinic_appointments

def create_clinic_user_reminders(n,clinic_appoinments):
    fake: Faker = Faker()   
    clinic_user_reminders = []
    for i in range(n):
        clinic_appoinment = random.choice(clinic_appoinments)
        clinic_user_reminder = ClinicUserReminders.objects.create(
            clinic=clinic_appoinment.clinic,
            reminder_to = fake.name(),
            date = fake.date_this_year(),
            is_sent = fake.boolean(),
            time = fake.date_time_this_year(),
            reminder_appointment = clinic_appoinment,
            reminder_description = fake.text(),
        )
        clinic_user_reminders.append(clinic_user_reminder)
    return clinic_user_reminders

def create_tasks(n,clinics,slps):
    fake: Faker = Faker()
    tasks = []
    for i in range(n):
        clinic = clinics[i%10]
        slp = slps[i%10]
        task = Tasks.objects.create(
            clinic=clinic,
            status=random.choice(["Pending", "Completed","Declined"]),
            task_name=fake.name(),
            description=fake.text(),
            slp=slp,
        )
        tasks.append(task)
    return tasks

def create_therapy_data(n,users,slps):
    fake: Faker = Faker()
    therapy_datas = []
    for i in range(n):
        therapy_data = TherapyData.objects.create(
            user=random.choice(users),
            objective = fake.sentence(),
            patient_name = fake.name(),
            slp_name = fake.name(),
            resources = fake.text(),
            observations = fake.text(),
            condition = fake.text(),
            criterion = fake.text(),
            performance = fake.text(),
            slp=random.choice(slps),
        )
        therapy_datas.append(therapy_data)
    return therapy_datas

def create_treatment_data(n,users,slps):
    fake: Faker = Faker()
    treatment_datas = []
    for i in range(n):
        treatment_data = TreatmentData.objects.create(
            user=random.choice(users),
            interventions = fake.text(),
            diagnosis_name = fake.name(),
            therapist_name = fake.name(),
            patient_age = random.randint(6, 80),
            goal = fake.text(),
            patient_name = fake.name(),
            slp=random.choice(slps),
            date = fake.date_time_this_year(),
        )
        treatment_datas.append(treatment_data)
    return treatment_datas

def create_notification(n,users):
    fake: Faker = Faker()
    notifications = []
    for i in range(n):
        notification = Notification.objects.create(
            user=random.choice(users),
            is_read = fake.boolean(),
            time = fake.date_time_this_year(),
            message = fake.text(),
            notification_type = random.choice(["New Appointment", "Canceled Appointment","Low Utilization","Rescheduled Appointment"]),
            sections = random.choice(["Patient","SLP","Sales Director","clinics","Sales"]),
        )
        notifications.append(notification)
    return notifications

def create_payments(n,users,subscriptions):
    fake: Faker = Faker()
    payments = []
    for i in range(n):
        subscription = random.choice(subscriptions)
        payment = Payment.objects.create(
            plan = subscription.subscription_name,
            payment_method = random.choice(["Credit Card", "Debit Card","PayPal"]),
            owner_name = fake.name(),
            owner_email = fake.email(),
            payment_method_id = fake.credit_card_number(),
            invoice_id = random.randint(1, 9999999999),
            subscription = subscription,
            status = random.choice(["Active", "Expired","Cancelled"]),
            payment_date = fake.date_this_year(),
            amount = subscription.subscription_price,
            user=random.choice(users),
            user_payment_id = random.randint(1,10000000000000),
            payment_status = random.choice(["Paid", "Unpaid"]),
            subscription_start_date = fake.date_this_year(),
            subscription_end_date = fake.date_this_year(),
            payment_failures = random.randint(1,10),
            has_used_trial = fake.boolean(),
        )
        payments.append(payment)
    return payments

def create_invoices(n,payments,clinics):
    fake: Faker = Faker()
    invoices = []
    for i in range(n):
        payment = random.choice(payments)
        invoice = Invoice.objects.create(
            paid_amount = payment.amount,
            due_date = fake.date_this_year(),
            subscription_count = random.randint(1, 10),
            subscription_type = payment.plan,
            customer_name = fake.name(),
            customer_email = fake.email(),
            invoice_status = random.choice(["Paid", "Unpaid"]),
            user = payment.user,
            subscription = payment.subscription,
            clinic= random.choice(clinics),
            issue_date = fake.date_this_year(),
            amount = payment.amount,
        )
        invoices.append(invoice)
    return invoices

def create_coupons(n,users):
    fake: Faker = Faker()
    coupons = []
    for i in range(n):
        coupon = Coupon.objects.create(
            free_trial = 7,
            is_used = fake.boolean(),
            code = fake.text(),
            user_type = "patient",
            user = users[i%20+21],
            discount = 100,
            expiration_date = fake.date_this_year(),
            redemption_count = 1,
        )
        coupons.append(coupon)
    return coupons

if __name__ == "__main__":
    import os

    from django.core.wsgi import get_wsgi_application

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
    application = get_wsgi_application()
    
    import random
    from faker import Faker
    from authentication.models import CustomUser,UserProfile,UserFiles,UserExercises,UsersInsurance
    from payment.models import Subscriptions,Payment,Invoice,Coupon
    from clinic.models import Disorders,Sessions,SessionType,PatientFiles,AssessmentResults,DemoRequested,Clinics,ClinicAppointments,ClinicUserReminders,Tasks,TherapyData,TreatmentData
    from sales_person.models import SalePersons,SalesTarget,SalePersonActivityLog,SalePersonPipeline
    from sales_director.models import SalesDirector,Sales
    from slp.models import Slps,SlpAppointments
    from notifications.models import Notification

    users = create_users(100)
    subscriptions = create_subscriptions()
    disorders = create_disorders()
    user_profiles =create_profiles(users)
    user_files = create_user_files(users)
    session_types = create_session_type()
    sessions = create_sessions(users, disorders,session_types)
    usser_excerises = create_user_excerise(100,sessions,disorders,users)
    user_insurances = create_users_insurance(100,users)
    #user 1 -10 sale person
    sale_persons = create_sale_persons(users,subscriptions)
    sales_targets = create_sales_targets(10,sale_persons)
    sale_person_activity_logs = create_sale_person_activity_logs(10,sale_persons)
    sale_person_pipelines = create_sale_person_pipelines(sale_persons)
    # 11 - 20 sales director
    sales_director = create_sales_directors(users)
    # 21-50 patients
    patient_files = create_patient_files(users,20,50)
    assessment_results = create_assessment_results(users,sessions,disorders,150)
    demo_requests = create_demo_requests(20,sale_persons)
    # 51-70 clinics
    clinics = create_clinics(20,users,sale_persons)
    # 81-90 slp
    slps = create_slps(10,users,clinics)
    slp_appointments = create_slp_appoinments(30,users,slps,disorders)
    # 91-100 sales
    sales = create_sales(30,clinics)
    clinic_appoinments = create_clinic_appointments(200,users,clinics,slps,disorders)
    clinic_user_reminders = create_clinic_user_reminders(100,clinic_appoinments)
    tasks = create_tasks(100,clinics,slps)
    therapy_data = create_therapy_data(100,users,slps)
    treatment_data = create_treatment_data(100,users,slps)
    notification = create_notification(500,users)
    payments = create_payments(100,users,subscriptions)
    invoice = create_invoices(100,payments,clinics)
    coupons = create_coupons(100,users)

    