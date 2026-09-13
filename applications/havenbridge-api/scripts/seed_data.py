"""
Seed realistic synthetic data for the HavenBridge application.

The script is designed to be repeatable. Existing records are left in place
so rerunning the script does not create duplicates.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_engine
from app.models import (
    Client,
    Coordinator,
    InquiryStatusHistory,
    ServiceCategory,
    ServiceInquiry,
)


SERVICE_CATEGORIES = [
    {
        "name": "Home Care",
        "description": (
            "In-home assistance and support services for individuals "
            "who need help with daily living."
        ),
    },
    {
        "name": "Respite Care",
        "description": (
            "Temporary support that provides relief for family members "
            "and primary caregivers."
        ),
    },
    {
        "name": "Disability Support",
        "description": (
            "Programs and assistance for individuals living with "
            "physical or developmental disabilities."
        ),
    },
    {
        "name": "Family Support",
        "description": (
            "Resources and coordinated support services for individuals "
            "and their families."
        ),
    },
    {
        "name": "Employee Resources",
        "description": (
            "Support services and resources available to employees "
            "and care teams."
        ),
    },
    {
        "name": "Residential Care",
        "description": (
            "Supported residential services for individuals requiring "
            "ongoing assistance."
        ),
    },
    {
        "name": "Community Access",
        "description": (
            "Programs that help individuals participate in community "
            "activities and services."
        ),
    },
]


CLIENTS = [
    {
        "first_name": "Jordan",
        "last_name": "Mensah",
        "email": "jordan.mensah@example.org",
        "phone": "780-555-0101",
        "city": "Edmonton",
    },
    {
        "first_name": "Amara",
        "last_name": "Okafor",
        "email": "amara.okafor@example.org",
        "phone": "780-555-0102",
        "city": "Edmonton",
    },
    {
        "first_name": "Daniel",
        "last_name": "Chen",
        "email": "daniel.chen@example.org",
        "phone": "403-555-0103",
        "city": "Calgary",
    },
    {
        "first_name": "Sofia",
        "last_name": "Martinez",
        "email": "sofia.martinez@example.org",
        "phone": "403-555-0104",
        "city": "Calgary",
    },
    {
        "first_name": "Noah",
        "last_name": "Williams",
        "email": "noah.williams@example.org",
        "phone": "587-555-0105",
        "city": "Red Deer",
    },
    {
        "first_name": "Priya",
        "last_name": "Sharma",
        "email": "priya.sharma@example.org",
        "phone": "587-555-0106",
        "city": "Edmonton",
    },
    {
        "first_name": "Samuel",
        "last_name": "Adebayo",
        "email": "samuel.adebayo@example.org",
        "phone": "780-555-0107",
        "city": "Edmonton",
    },
    {
        "first_name": "Grace",
        "last_name": "Thompson",
        "email": "grace.thompson@example.org",
        "phone": "403-555-0108",
        "city": "Lethbridge",
    },
    {
        "first_name": "Michael",
        "last_name": "Singh",
        "email": "michael.singh@example.org",
        "phone": "780-555-0109",
        "city": "Fort McMurray",
    },
    {
        "first_name": "Avery",
        "last_name": "Brown",
        "email": "avery.brown@example.org",
        "phone": "587-555-0110",
        "city": "Grande Prairie",
    },
    {
        "first_name": "Fatima",
        "last_name": "Hassan",
        "email": "fatima.hassan@example.org",
        "phone": "780-555-0111",
        "city": "Edmonton",
    },
    {
        "first_name": "Ethan",
        "last_name": "Wilson",
        "email": "ethan.wilson@example.org",
        "phone": "403-555-0112",
        "city": "Calgary",
    },
    {
        "first_name": "Chiamaka",
        "last_name": "Nwosu",
        "email": "chiamaka.nwosu@example.org",
        "phone": "587-555-0113",
        "city": "Edmonton",
    },
    {
        "first_name": "Lucas",
        "last_name": "Martin",
        "email": "lucas.martin@example.org",
        "phone": "403-555-0114",
        "city": "Medicine Hat",
    },
    {
        "first_name": "Maya",
        "last_name": "Patel",
        "email": "maya.patel@example.org",
        "phone": "780-555-0115",
        "city": "Sherwood Park",
    },
    {
        "first_name": "Benjamin",
        "last_name": "Taylor",
        "email": "benjamin.taylor@example.org",
        "phone": "587-555-0116",
        "city": "St. Albert",
    },
    {
        "first_name": "Aisha",
        "last_name": "Bello",
        "email": "aisha.bello@example.org",
        "phone": "780-555-0117",
        "city": "Edmonton",
    },
    {
        "first_name": "Oliver",
        "last_name": "Anderson",
        "email": "oliver.anderson@example.org",
        "phone": "403-555-0118",
        "city": "Airdrie",
    },
    {
        "first_name": "Nadia",
        "last_name": "Khan",
        "email": "nadia.khan@example.org",
        "phone": "587-555-0119",
        "city": "Edmonton",
    },
    {
        "first_name": "Gabriel",
        "last_name": "Rodriguez",
        "email": "gabriel.rodriguez@example.org",
        "phone": "403-555-0120",
        "city": "Calgary",
    },
]


COORDINATORS = [
    {
        "first_name": "Olivia",
        "last_name": "Bennett",
        "email": "olivia.bennett@havenbridge.example.org",
        "team": "Home and Community Services",
    },
    {
        "first_name": "Marcus",
        "last_name": "Johnson",
        "email": "marcus.johnson@havenbridge.example.org",
        "team": "Home and Community Services",
    },
    {
        "first_name": "Amina",
        "last_name": "Yusuf",
        "email": "amina.yusuf@havenbridge.example.org",
        "team": "Family and Respite Services",
    },
    {
        "first_name": "Claire",
        "last_name": "Robertson",
        "email": "claire.robertson@havenbridge.example.org",
        "team": "Family and Respite Services",
    },
    {
        "first_name": "David",
        "last_name": "Kim",
        "email": "david.kim@havenbridge.example.org",
        "team": "Disability Support Services",
    },
    {
        "first_name": "Ngozi",
        "last_name": "Eze",
        "email": "ngozi.eze@havenbridge.example.org",
        "team": "Disability Support Services",
    },
    {
        "first_name": "Rachel",
        "last_name": "Morgan",
        "email": "rachel.morgan@havenbridge.example.org",
        "team": "Residential Services",
    },
    {
        "first_name": "Jason",
        "last_name": "Lee",
        "email": "jason.lee@havenbridge.example.org",
        "team": "Community Access Services",
    },
]


SERVICE_INQUIRIES = [
    {
        "client_email": "jordan.mensah@example.org",
        "category": "Home Care",
        "coordinator_email": "olivia.bennett@havenbridge.example.org",
        "status": "reviewing",
        "message": (
            "I am looking for information about weekly in-home support "
            "for an older family member who needs help with daily activities."
        ),
    },
    {
        "client_email": "amara.okafor@example.org",
        "category": "Respite Care",
        "coordinator_email": "amina.yusuf@havenbridge.example.org",
        "status": "referred",
        "message": (
            "Our family is looking for weekend respite support for a "
            "relative who requires regular supervision."
        ),
    },
    {
        "client_email": "daniel.chen@example.org",
        "category": "Disability Support",
        "coordinator_email": "david.kim@havenbridge.example.org",
        "status": "reviewing",
        "message": (
            "I would like information about community-based disability "
            "support and assistance with independent living."
        ),
    },
    {
        "client_email": "sofia.martinez@example.org",
        "category": "Family Support",
        "coordinator_email": "claire.robertson@havenbridge.example.org",
        "status": "closed",
        "message": (
            "I am looking for family support resources and guidance on "
            "available community programs."
        ),
    },
    {
        "client_email": "noah.williams@example.org",
        "category": "Community Access",
        "coordinator_email": None,
        "status": "new",
        "message": (
            "I would like to learn about programs that support participation "
            "in recreational and community activities."
        ),
    },
    {
        "client_email": "priya.sharma@example.org",
        "category": "Residential Care",
        "coordinator_email": "rachel.morgan@havenbridge.example.org",
        "status": "reviewing",
        "message": (
            "Our family is exploring supported residential options and "
            "would like to understand eligibility and available services."
        ),
    },
    {
        "client_email": "samuel.adebayo@example.org",
        "category": "Home Care",
        "coordinator_email": "marcus.johnson@havenbridge.example.org",
        "status": "referred",
        "message": (
            "I need information about home care assistance following "
            "a recent change in my family member's support needs."
        ),
    },
    {
        "client_email": "grace.thompson@example.org",
        "category": "Respite Care",
        "coordinator_email": None,
        "status": "new",
        "message": (
            "I am requesting information about short-term respite options "
            "for a family caregiver."
        ),
    },
    {
        "client_email": "michael.singh@example.org",
        "category": "Employee Resources",
        "coordinator_email": None,
        "status": "new",
        "message": (
            "I would like information about employee wellness resources "
            "and support programs available to care staff."
        ),
    },
    {
        "client_email": "avery.brown@example.org",
        "category": "Community Access",
        "coordinator_email": "jason.lee@havenbridge.example.org",
        "status": "reviewing",
        "message": (
            "I am interested in supported community outings and social "
            "programs available in my area."
        ),
    },
    {
        "client_email": "fatima.hassan@example.org",
        "category": "Family Support",
        "coordinator_email": "amina.yusuf@havenbridge.example.org",
        "status": "referred",
        "message": (
            "Our family needs help identifying community resources and "
            "coordinating support for a dependent adult."
        ),
    },
    {
        "client_email": "ethan.wilson@example.org",
        "category": "Home Care",
        "coordinator_email": None,
        "status": "new",
        "message": (
            "I am looking for information about assistance with meals, "
            "mobility and daily routines at home."
        ),
    },
    {
        "client_email": "chiamaka.nwosu@example.org",
        "category": "Disability Support",
        "coordinator_email": "ngozi.eze@havenbridge.example.org",
        "status": "reviewing",
        "message": (
            "I would like to discuss disability support programs and "
            "options for building greater independence."
        ),
    },
    {
        "client_email": "lucas.martin@example.org",
        "category": "Residential Care",
        "coordinator_email": "rachel.morgan@havenbridge.example.org",
        "status": "closed",
        "message": (
            "I requested information about supported residential care "
            "and placement options for a family member."
        ),
    },
    {
        "client_email": "maya.patel@example.org",
        "category": "Respite Care",
        "coordinator_email": "claire.robertson@havenbridge.example.org",
        "status": "reviewing",
        "message": (
            "I am looking for scheduled respite support to help our family "
            "manage ongoing caregiving responsibilities."
        ),
    },
    {
        "client_email": "benjamin.taylor@example.org",
        "category": "Community Access",
        "coordinator_email": "jason.lee@havenbridge.example.org",
        "status": "referred",
        "message": (
            "I would like information about transportation and supported "
            "access to community programs."
        ),
    },
    {
        "client_email": "aisha.bello@example.org",
        "category": "Family Support",
        "coordinator_email": None,
        "status": "new",
        "message": (
            "I am seeking information about family support services and "
            "help navigating available local resources."
        ),
    },
    {
        "client_email": "oliver.anderson@example.org",
        "category": "Disability Support",
        "coordinator_email": "david.kim@havenbridge.example.org",
        "status": "closed",
        "message": (
            "I requested assistance identifying disability support "
            "programs and service eligibility requirements."
        ),
    },
    {
        "client_email": "nadia.khan@example.org",
        "category": "Home Care",
        "coordinator_email": "olivia.bennett@havenbridge.example.org",
        "status": "reviewing",
        "message": (
            "I would like to arrange an assessment for possible in-home "
            "support for a family member."
        ),
    },
    {
        "client_email": "gabriel.rodriguez@example.org",
        "category": "Residential Care",
        "coordinator_email": "rachel.morgan@havenbridge.example.org",
        "status": "referred",
        "message": (
            "I am requesting information about residential support options "
            "and the referral process."
        ),
    },
]


def seed_service_categories() -> None:
    """Insert missing HavenBridge service categories."""

    with Session(get_engine()) as db:
        existing_names = set(
            db.scalars(
                select(ServiceCategory.name)
            ).all()
        )

        inserted = 0

        for category in SERVICE_CATEGORIES:
            if category["name"] in existing_names:
                continue

            db.add(
                ServiceCategory(
                    name=category["name"],
                    description=category["description"],
                )
            )

            inserted += 1

        db.commit()

    print(f"Service categories inserted: {inserted}")


def seed_clients() -> None:
    """Insert missing synthetic HavenBridge clients."""

    with Session(get_engine()) as db:
        existing_emails = set(
            db.scalars(
                select(Client.email)
            ).all()
        )

        inserted = 0

        for client in CLIENTS:
            if client["email"] in existing_emails:
                continue

            db.add(Client(**client))
            inserted += 1

        db.commit()

    print(f"Clients inserted: {inserted}")


def seed_coordinators() -> None:
    """Insert missing synthetic HavenBridge coordinators."""

    with Session(get_engine()) as db:
        existing_emails = set(
            db.scalars(
                select(Coordinator.email)
            ).all()
        )

        inserted = 0

        for coordinator in COORDINATORS:
            if coordinator["email"] in existing_emails:
                continue

            db.add(Coordinator(**coordinator))
            inserted += 1

        db.commit()

    print(f"Coordinators inserted: {inserted}")


def seed_service_inquiries() -> None:
    """
    Insert realistic relational service inquiries.

    Existing inquiry/email + message combinations are skipped so the seed
    script can be run repeatedly without creating duplicate inquiries.
    """

    with Session(get_engine()) as db:
        clients_by_email = {
            client.email: client
            for client in db.scalars(
                select(Client)
            ).all()
        }

        categories_by_name = {
            category.name: category
            for category in db.scalars(
                select(ServiceCategory)
            ).all()
        }

        coordinators_by_email = {
            coordinator.email: coordinator
            for coordinator in db.scalars(
                select(Coordinator)
            ).all()
        }

        existing_inquiries = {
            (email, message)
            for email, message in db.execute(
                select(
                    ServiceInquiry.requester_email,
                    ServiceInquiry.message,
                )
            ).all()
        }

        inserted = 0

        for inquiry_data in SERVICE_INQUIRIES:
            client = clients_by_email[inquiry_data["client_email"]]
            category = categories_by_name[inquiry_data["category"]]

            coordinator_email = inquiry_data["coordinator_email"]

            coordinator = (
                coordinators_by_email[coordinator_email]
                if coordinator_email is not None
                else None
            )

            inquiry_key = (
                client.email,
                inquiry_data["message"],
            )

            if inquiry_key in existing_inquiries:
                continue

            inquiry = ServiceInquiry(
                requester_name=f"{client.first_name} {client.last_name}",
                requester_email=client.email,
                service_category=category.name,
                message=inquiry_data["message"],
                status=inquiry_data["status"],
                client_id=client.id,
                category_id=category.id,
                coordinator_id=(
                    coordinator.id
                    if coordinator is not None
                    else None
                ),
            )

            db.add(inquiry)
            inserted += 1

        db.commit()

    print(f"Service inquiries inserted: {inserted}")


def seed_inquiry_status_history() -> None:
    """
    Create one initial history record for each relational service inquiry.

    Existing history is preserved so rerunning the seed script does not
    create duplicate status-history records.
    """

    with Session(get_engine()) as db:
        existing_inquiry_ids = set(
            db.scalars(
                select(InquiryStatusHistory.inquiry_id)
            ).all()
        )

        relational_inquiries = db.scalars(
            select(ServiceInquiry).where(
                ServiceInquiry.client_id.is_not(None)
            )
        ).all()

        inserted = 0

        for inquiry in relational_inquiries:
            if inquiry.id in existing_inquiry_ids:
                continue

            db.add(
                InquiryStatusHistory(
                    inquiry_id=inquiry.id,
                    old_status=None,
                    new_status=inquiry.status,
                    changed_by="seed",
                )
            )

            inserted += 1

        db.commit()

    print(f"Inquiry status history inserted: {inserted}")

if __name__ == "__main__":
    seed_service_categories()
    seed_clients()
    seed_coordinators()
    seed_service_inquiries()
    seed_inquiry_status_history()
