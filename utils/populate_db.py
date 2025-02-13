import random
from faker import Faker
from authentication.models import CustomUser, UserProfile
from clinic.models import Clinics, Disorders, Sessions, SessionType
from slp.models import Slps  # Assuming `Slps` model exists
from sales_person.models import SalePersons  # Assuming `SalePersons` model exists

fake = Faker()

def create_users(n=10):
    users = []
    for _ in range(n):
        user = Users.objects.create(
            username=fake.user_name(),
            email=fake.email(),
            user_id=random.randint(1000, 9999),
            password_hash=fake.password(),
            user_type=random.choice(["admin", "patient", "therapist"]),
            verified=fake.boolean(),
        )
        users.append(user)
    return users

def create_profiles(users):
    for user in users:
        UserProfile.objects.create(
            user_id=user,
            full_name=fake.name(),
            gender=random.choice(["Male", "Female", "Other"]),
            country=fake.country(),
            state=fake.state(),
            status=random.choice(["Active", "Inactive"]),
            patient_status=random.choice(["New", "Returning"]),
            slp_id=Slps.objects.order_by("?").first(),
        )

def create_clinics(n=5):
    clinics = []
    for _ in range(n):
        clinic = Clinics.objects.create(
            clinic_id=random.randint(1000, 9999),
            clinic_name=fake.company(),
            address=fake.address(),
            email=fake.email(),
            phone=random.randint(1000000000, 9999999999),
            ein_number=random.randint(100000, 999999),
            state=fake.state(),
            country=fake.country(),
            sale_person_id=SalePersons.objects.order_by("?").first(),
            user_id=Users.objects.order_by("?").first(),
        )
        clinics.append(clinic)
    return clinics

def create_disorders(n=5):
    disorders = []
    for _ in range(n):
        disorder = Disorders.objects.create(
            disorder_id=random.randint(1000, 9999),
            disorder_name=fake.word()
        )
        disorders.append(disorder)
    return disorders

def create_sessions(users, disorders):
    for _ in range(10):
        Sessions.objects.create(
            session_id=random.randint(1000, 9999),
            session_status=random.choice(["Scheduled", "Completed", "Canceled"]),
            user_id=random.choice(users),
            session_type_id=SessionType.objects.order_by("?").first(),
            start_time=fake.date_time_this_year(),
            end_time=fake.date_time_this_year(),
            disorder_id=random.choice(disorders),
        )

def run():
    users = create_users(10)
    create_profiles(users)
    create_clinics(5)
    disorders = create_disorders(5)
    create_sessions(users, disorders)
    print("Fake data inserted successfully!")

if __name__ == "__main__":
    run()
