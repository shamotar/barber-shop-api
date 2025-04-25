import datetime
import jinja2

from core.config import settings
from modules.email.email_operations import EmailOperations
from modules.user.models import User


class EmailService:
    def __init__(self, email_operations: EmailOperations):
        self.email_operations = email_operations
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(searchpath="modules/email/templates"),
            autoescape=jinja2.select_autoescape(["html", "xml"]),
        )

    async def send_barber_cancellation_email(
        self,
        barber: User,
        client_name: User,
        service_name: str,
        appointment_date: datetime.date,
        appointment_time: datetime.time,
    ) -> None:
        """
        Send an email to the barber notifying them of a cancellation.
        """
        template = "barber_cancellation_email.html"
        subject = "Appointment Cancellation Notification"
        body = self.env.get_template(template).render(
            barber_name=barber.firstName,
            client_name=f"{client_name.firstName} {client_name.lastName}",
            service_name=service_name,
            appointment_date=appointment_date.strftime('%B %d, %Y'),
            appointment_time=appointment_time.strftime('%I:%M %p'),
            appointments_url=f"{settings.get_config()['frontend_host']}/appointments",
        )
        await self.email_operations.send_email(
            email=barber.email,
            subject=subject,
            body=body,
        )

    async def send_client_cancellation_email(
        self,
        barber: User,
        client: User,
        service_name: str,
        appointment_date: datetime.date,
        appointment_time: datetime.time,
    ) -> None:
        """
        Send an email to the client notifying them of a cancellation.
        """
        template = "client_cancellation_email.html"
        subject = "Appointment Cancellation Notification"
        body = self.env.get_template(template).render(
            barber_name=f"{barber.firstName} {barber.lastName}",
            client_name=f"{client.firstName}",
            service_name=service_name,
            appointment_date=appointment_date.strftime('%B %d, %Y'),
            appointment_time=appointment_time.strftime('%I:%M %p'),
        )
        await self.email_operations.send_email(
            email=client.email,
            subject=subject,
            body=body,
        )

    

