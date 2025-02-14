import random
from faker import Faker
from authentication.models import CustomUser, UserProfile,UserFiles,UserExercises,UsersInsurance
from clinic.models import Clinics, Disorders, Sessions, SessionType,ClinicAppointments,ClinicUserReminders,DemoRequested,PatientFiles,Tasks,TherapyData,AssessmentResults,TreatmentData
from slp.models import Slps,SlpAppointments  # Assuming `Slps` model exists
from sales_person.models import SalePersons  # Assuming `SalePersons` model exists
from payment.models import Subscriptions  # Assuming `Subscriptions` model exists
from sales_director.models import SalesDirector ,Sales # Assuming `SalesDirector` model exists,
from sales_person.models import SalesTarget,SalePersonActivityLog,SalePersonPipeline
fake = Faker()

def create_users(n=10):
    users = []
    for i in range(n):
        user = CustomUser.objects.create(
            username=fake.user_name(),
            email=fake.email(),
            user=i,
            password_hash=fake.password(),
            user_type=random.choice(["admin", "slp", "sale_person","clinic","sales_director"]),
            verified=fake.boolean(),
        )
        users.append(user)
    print(users)
    return users

def create_profiles(users):
    profiles = []
    for user in users:
        profile =UserProfile.objects.create(
            user=user,
            full_name=fake.name(),
            gender=random.choice(["Male", "Female", "Other"]),
            country=fake.country(),
            state=fake.state(),
            profile_id = random.randint(1000, 9999),
            status=random.choice(["Active", "Inactive"]),
            patient_status=random.choice(["New", "Returning"]),
            slp_id=Slps.objects.order_by("?").first(),
            age=random.randint(6, 80),
        )
        profiles.append(profile)
    return profiles


def create_clinics(n=5):
    clinics = []
    for i in range(n):
        clinic = Clinics.objects.create(
            clinic_id=i,
            clinic_name=fake.company(),
            address=fake.address(),
            email=fake.email(),
            phone=random.randint(1000000000, 9999999999),
            ein_number=random.randint(100000, 999999),
            state=fake.state(),
            country=fake.country(),
            sale_person_id=SalePersons.objects.order_by("?").first(),
            user_id=CustomUser.objects.order_by("?").first(),
        )
        clinics.append(clinic)
    return clinics

def create_slps(n=10):
    slps = []
    for i in range(n):
        slp = Slps.objects.create(
            slp_id=i,
            profile_image_path=fake.image_url(),
            status=random.choice(["Active", "Inactive"]),
            country=fake.country(),
            state=fake.state(),
            email=fake.email(),
            slp_name=fake.name(),
            user_id=CustomUser.objects.order_by("?").first(),
            clinic_id=Clinics.objects.order_by("?").first(),
            phone=random.randint(1000000000, 9999999999),
        )
        slps.append(slp)
    return slps

def create_slp_appointments(n=10):
    slp_appointments = []
    for i in range(n):
        slp_appointment = SlpAppointments.objects.create(
            appointment_id=i,
            disorder_id=Disorders.objects.order_by("?").first(),
            slp_id=Slps.objects.order_by("?").first(),
            user_id=CustomUser.objects.order_by("?").first(),
            appointment_date=fake.date_this_year(),
            session_type=random.choice(["Initial", "Follow-up"]),
            appointment_status=random.choice(["Scheduled", "Cancelled"]),
            start_time=fake.date_time_this_year(),
            end_time=fake.date_time_this_year(),
        )
        slp_appointments.append(slp_appointment)
    return slp_appointments

def create_sale_persons(n=10):
    sale_persons = []
    for i in range(n):
        sale_person = SalePersons.objects.create(
            sale_person_id=i,
            phone=random.randint(1000000000, 9999999999),
            state=fake.state(),
            country=fake.country(),
            status=random.choice(["Active", "Inactive"]),
            user_id=CustomUser.objects.order_by("?").first(),
            subscription_id=Subscriptions.objects.order_by("?").first(),
            subscription_count=random.randint(1, 10),
            commission_percent=random.randint(1, 10),
        )
        sale_persons.append(sale_person)
    return sale_persons

def create_sales_targets(n=10):
    sales_targets = []
    for i in range(n):
        sales_target = SalesTarget.objects.create(
            id=i,
            sale_person_id=SalePersons.objects.order_by("?").first(),
            month=random.randint(1, 12),
            year=random.randint(2010, 2020),
            target=random.randint(1000, 9999),
        )
        sales_targets.append(sales_target)
    return sales_targets
def create_sale_person_activity_logs(n=10):
    sale_person_activity_logs = []
    for i in range(n):
        sale_person_activity_log = SalePersonActivityLog.objects.create(
            sale_person_activity_log_id=i,
            sale_person_id=SalePersons.objects.order_by("?").first(),
            meetings=random.randint(1, 10),
            qualifying_calls=random.randint(1, 10),
            renewal_calls=random.randint(1, 10),
            proposals_sent=random.randint(1, 10),
            date=fake.date_time_this_year(),
        )
        sale_person_activity_logs.append(sale_person_activity_log)
    return sale_person_activity_logs

def create_sale_person_pipelines(n=10):
    sale_person_pipelines = []
    for i in range(n):
        sale_person_pipeline = SalePersonPipeline.objects.create(
            sale_person_pipeline_id=i,
            sale_person_id=SalePersons.objects.order_by("?").first(),
            qualified_sales=random.randint(1, 10),
            renewals=random.randint(1, 10),
            prospective_sales=random.randint(1, 10),
            closed_sales=random.randint(1, 10),
            date=fake.date_time_this_year(),
        )
        sale_person_pipelines.append(sale_person_pipeline)
    return sale_person_pipelines

def create_sales_directors(n=10):
    sales_directors = []
    for i in range(n):
        sales_director = SalesDirector.objects.create(
            sales_director_id=i,
            user_id=CustomUser.objects.order_by("?").first(),
            department=fake.company(),
            designation=fake.job(),
        )
        sales_directors.append(sales_director)
    return sales_directors

def create_sales(n=10):
    sales = []
    for i in range(n):
        sale = Sales.objects.create(
            sales_id=i,
            sale_person_id=SalePersons.objects.order_by("?").first(),
            subscription_count=random.randint(1, 10),
            commission_percent=random.randint(1, 10),
            clinic_id=Clinics.objects.order_by("?").first(),
            payment_status=random.choice(["Paid", "Unpaid"]),
            subscription_type=random.choice(["Monthly", "Yearly"]),
        )
        sales.append(sale)
    return sales


def create_disorders(n=5):
    disorders = []
    disorder_name = ["stammering","receptive","voice","expressive","articulation"]
    for i in range(n):
        disorder = Disorders.objects.create(
            disorder_id=i,
            disorder_name=disorder_name[i]
        )
        disorders.append(disorder)
    return disorders

def create_session_types(n=5):
    session_types = []
    session_type_name = ["Initial","Follow-up"]
    for i in range(n):
        session_type = SessionType.objects.create(
            session_type_id=i,
            type_name=session_type_name[i%2],
        )
        session_types.append(session_type)
    return session_types

def create_sessions(users, disorders):
    for i in range(10):
        Sessions.objects.create(
            session_id=i,
            session_status=random.choice(["Completed", "quick_assessment_status"]),
            user_id=random.choice(users),
            session_type_id=SessionType.objects.order_by("?").first(),
            start_time=fake.date_time_this_year(),
            end_time=fake.date_time_this_year(),
            disorder_id=random.choice(disorders),
        )


def create_user_files(n=10):
    user_files = []
    for i in range(n):
        user_file = UserFiles.objects.create(
            file_id=i,
            role=random.choice(["admin", "slp", "sale_person","clinic","sales_director"]),
            file_path=fake.file_path(),
            user=CustomUser.objects.order_by("?").first(),
            upload_timestamp=fake.date_time_this_year(),
            file_name=fake.file_name(),
        )
        user_files.append(user_file)
    return user_files

def create_user_exercises(n=10):
    user_exercises = []
    for i in range(n):
        user_exercise = UserExercises.objects.create(
            total_questions=random.randint(1, 100),
            user_exercise_id=i,
            level_name=fake.name(),
            world_id=random.randint(1, 100),
            sound_id=random.randint(1, 100),
            session_id=Sessions.objects.order_by("?").first(),
            sound_id_list=fake.text(),
            disorder_id=Disorders.objects.order_by("?").first(),
            user=CustomUser.objects.order_by("?").first(),
            completion_status=random.choice(["Completed", "Incomplete"]),
            exercise_date=fake.date_time_this_year(),
            score=random.randint(0, 100),
            emotion=random.choice(["Happy", "Sad", "Angry"]),
            completed_questions=random.randint(1, 100),
        )
        user_exercises.append(user_exercise)
    return user_exercises
def create_clinic_appointments(n=10):
    clinic_appoinments = []
    for i in range(n):
        clinic_appoinment = ClinicAppointments.objects.create(
            appointment_id=i,
            slp_id=Slps.objects.order_by("?").first(),
            clinic_id=Clinics.objects.order_by("?").first(),
            session_type=random.choice(["Initial", "Follow-up"]),
            appointment_status=random.choice(["Scheduled", "Cancelled"]),
            appointment_date=fake.date_this_year(),
            appointment_start=fake.date_time_this_year(),
            appointment_end=fake.date_time_this_year(),
            disorder_id=Disorders.objects.order_by("?").first(),
            user_id=CustomUser.objects.order_by("?").first(),
        )
        clinic_appoinments.append(clinic_appoinment)
    return clinic_appoinments

def create_users_insurance(n=10):
    users_insurance = []
    for i in range(n):
        user_insurance = UsersInsurance.objects.create(
            cpt_number=fake.uri_extension(),
            user=CustomUser.objects.order_by("?").first(),
            insurance_provider=fake.company(),
            insurance_status=random.choice(["Active", "Inactive"]),
            policy_number=random.randint(100000, 999999),
            insurance_id=i,
            claim_date=fake.date_this_year(),
        )
        users_insurance.append(user_insurance)
    return users_insurance

def clinic_user_reminders(n=10):
    clinic_user_reminders = []
    for i in range(n):
        clinic_user_reminder = ClinicUserReminders.objects.create(
            reminder_id=i,
            reminder_to=fake.name(),
            date=fake.date_this_year(),
            is_sent=fake.boolean(),
            clinic_id=Clinics.objects.order_by("?").first(),
            time=fake.date_time_this_year(),
            reminder_appointment_id=ClinicAppointments.objects.order_by("?").first(),
            reminder_description=fake.text(),
        )
        clinic_user_reminders.append(clinic_user_reminder)
    return clinic_user_reminders

def create_tasks(n=10):
    tasks = []
    for i in range(n):
        task = Tasks.objects.create(
            task_id=i,
            clinic_id=Clinics.objects.order_by("?").first(),
            status=random.choice(["Active", "Inactive"]),
            task_name=fake.sentence(),
            description=fake.text(),
            slp_id=Slps.objects.order_by("?").first(),
        )
        tasks.append(task)
    return tasks

def create_demo_requests(n=20):
    demo_requests = []
    for i in range(n):
        demo_request = DemoRequested.objects.create(
            demo_request_id=i,
            clinic_name=fake.company(),
            first_name=fake.name(),
            last_name=fake.name(),
            country=fake.country(),
            comment=fake.text(),
            email=fake.email(),
            contact_number=random.randint(1000000000, 9999999999),
            sale_person_id=SalePersons.objects.order_by("?").first(),
            patient_count  = random.randint(1, 100),
        )
        demo_requests.append(demo_request)
    return demo_requests

def create_patient_files(n=10):
    patient_files = []
    for i in range(n):
        patient_file = PatientFiles.objects.create(
            file_id=i,
            file_name=fake.file_name(),
            document_type = fake.uri_extension(),
            diagnosis_name = fake.name(),
            role=random.choice(["Patient", "SLP"]),
            file_path=fake.file_path(),
            user_id=CustomUser.objects.order_by("?").first(),
            upload_timestamp=fake.date_time_this_year(),
        )
        patient_files.append(patient_file)
    return patient_files

def crete_therapy_data(n=10):
    therapy_data =[]
    for i in range(n):
        therapy_datum = TherapyData.objects.create(
            therapy_data_id=i,
            objective=fake.sentence(),
            patient_name=fake.name(),
            slp_name=fake.name(),
            observation=fake.text(),
            condition=fake.text(),
            criterion=fake.text(),
            slp_id=Slps.objects.order_by("?").first(),
            user_id = CustomUser.objects.order_by("?").first(),
        )
        therapy_data.append(therapy_datum)
    return therapy_data

def create_treatment_data(n=10):
    treatment_data =[]
    for i in range(n):
        treatment_datum = TreatmentData.objects.create(
            therapy_data_id=i,
            interventions=fake.text(),
            diagnosis_name=fake.name(),
            therapist_name=fake.name(),
            patient_age=random.randint(6, 80),
            goad=fake.text(),
            patient_name=fake.name(),
            slp_id=Slps.objects.order_by("?").first(),
            user_id = CustomUser.objects.order_by("?").first(),
        )
        treatment_data.append(treatment_datum)
    return treatment_data

def create_assessment_results(n=10):
    assessment_results =[]
    for i in range(n):
        assessment_result = AssessmentResults.objects.create(
            assessment_id=i,
            user_id = CustomUser.objects.order_by("?").first(),
            session_id=Sessions.objects.order_by("?").first(),
            score = random.randint(0, 100),
            disorder_id=Disorders.objects.order_by("?").first(),
        )
        assessment_results.append(assessment_result)
    return assessment_results

def run():
    users = create_users(10)
    create_profiles(users)
    create_clinics(5)
    disorders = create_disorders(5)
    create_sessions(users, disorders)
    create_user_files()
    create_user_exercises()
    create_clinic_appointments()
    create_users_insurance()
    create_slps()
    create_slp_appointments()
    create_sale_persons()
    create_sales_targets()
    create_sale_person_activity_logs()
    create_sale_person_pipelines()
    create_sales_directors()
    create_sales()
    clinic_user_reminders()
    create_session_types()
    create_tasks()
    create_demo_requests()
    create_patient_files()
    create_assessment_results()
    crete_therapy_data()
    create_treatment_data()
    print("Fake data inserted successfully!")

if __name__ == "__main__":
    run()
