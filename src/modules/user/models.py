from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship
)

from sqlalchemy import (
    String,
    Boolean,
    ForeignKey,
    Float,
    Time,
    DateTime,
    Integer,
    Enum,
    Text,
    Date,
    UniqueConstraint
)

from sqlalchemy.sql import func

import enum

from .barber_schema import BarberResponse
from .user_schema import UserResponse
from ..schedule_schema import ScheduleResponse, TimeSlotChildResponse
from .service_schema import ServiceResponse
from ..appointment_schema import AppointmentResponse

class Base(DeclarativeBase):
    pass

# Defining Enum to be used in Appointment table
class AppointmentStatus(enum.Enum):
    pending = 'pending'
    confirmed = 'confirmed'
    completed = 'completed'
    canceled = 'canceled'


# User model
class User(Base):
    __tablename__ = "user"
    
    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kc_id: Mapped[str] = mapped_column(String(50), primary_key=False)
    firstName: Mapped[str] = mapped_column(String(50), nullable=False)
    lastName: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(50), nullable=False)
    phoneNumber: Mapped[str] = mapped_column(String(10), nullable=False, unique=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    
    '''
    User class relationships
    '''

    # User can have one Barber (One-to-One)
    barber: Mapped["Barber"] = relationship(back_populates="user", uselist=False)
    
    # User can have many Appointments (One-to-Many)
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="user")
    
    # User have send many Threads (One-To-Many)
    sent_threads: Mapped[list["Thread"]] = relationship(foreign_keys="Thread.sendingUser", back_populates="sending_user")

    # User can receive many Threads (One-To-Many)
    received_threads: Mapped[list["Thread"]] = relationship(foreign_keys="Thread.receivingUser", back_populates="receiving_user")


    def to_response_schema(self) -> UserResponse:
        return UserResponse(
            user_id=self.user_id,
            firstName=self.firstName,
            lastName=self.lastName,
            email=self.email,
            phoneNumber=self.phoneNumber,
            is_admin=self.is_admin
        )

class Barber(Base):
    __tablename__ = "barber"
    
    barber_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.user_id", ondelete="CASCADE"), nullable=False, unique=True)
    
    '''
    Barber class relationships
    '''

    # Barber is linked to a single user (as specified by 'uselist = false' in User table above. One-to-One)
    user: Mapped["User"] = relationship(back_populates="barber", lazy="selectin")

    # Barber can have multiple Appointments (One-to-Many)
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="barber")

    # A Barber can have multiple Schedules (One-to-Many)
    schedules: Mapped[list["Schedule"]] = relationship(back_populates="barber")

    def to_response_schema(self) -> BarberResponse:
        return BarberResponse(
        barber_id=self.barber_id,
        user=UserResponse(
            user_id=self.user.user_id,
            firstName=self.user.firstName,
            lastName=self.user.lastName,
            email=self.user.email,
            phoneNumber=self.user.phoneNumber,
            is_admin=self.user.is_admin
        )
    )

class Appointment(Base):
    __tablename__ = "appointment"
    
    appointment_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    appointment_date: Mapped[Date] = mapped_column(Date, nullable=True, default=func.current_date())
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.user_id", ondelete="CASCADE"), nullable=False)
    barber_id: Mapped[int] = mapped_column(Integer, ForeignKey("barber.barber_id", ondelete="CASCADE"), nullable=False)
    status: Mapped[AppointmentStatus] = mapped_column(Enum(AppointmentStatus), nullable=False)
    
    '''
    Appointment class relationships
    '''

    # Each appointment is linked to one User (who booked it) - (Many-to-One)
    user: Mapped["User"] = relationship(back_populates="appointments", lazy="selectin")

    # Each appointment is assigned to one Barber (Many-to-One)
    barber: Mapped["Barber"] = relationship(back_populates="appointments", lazy="selectin")

    # An Appointment can have multiple AppointmentService records ()
    appointment_services: Mapped[list["AppointmentService"]] = relationship(back_populates="appointment", lazy="selectin", cascade="all, delete, delete-orphan")

     # Relationship to Appointment_TimeSlot (creates Many-to-Many with TimeSlot)
    appointment_time_slots: Mapped[list["Appointment_TimeSlot"]] = relationship("Appointment_TimeSlot", back_populates="appointment", lazy="selectin", cascade="all, delete, delete-orphan")

    def to_response_schema(self) -> AppointmentResponse:
        return AppointmentResponse(
            appointment_id=self.appointment_id,
            appointment_date=self.appointment_date.strftime("%Y-%m-%d") if self.appointment_date else None,
            user=self.user.to_response_schema(),
            barber=self.barber.to_response_schema(),
            status=self.status,
            time_slots=[
                time_slot.time_slot.to_response_schema() for time_slot in self.appointment_time_slots
            ],
            services=[
                service.service.to_response_schema() for service in self.appointment_services
            ]
        )

class Service(Base):
    __tablename__ = "service"
    
    service_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    duration: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[Float] = mapped_column(Float(5, 2), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    popularity_score: Mapped[int] = mapped_column(Integer, nullable=False)
    
    '''
    Service class relationships
    '''

    # A service can be linked to multiple AppointmentService records (One-to-Many)
    appointment_services: Mapped[list["AppointmentService"]] = relationship(back_populates="service")

    def to_response_schema(self) -> ServiceResponse:
        return ServiceResponse(
            service_id=self.service_id,
            name=self.name,
            duration=self.duration,
            price=self.price,
            category=self.category,
            description=self.description,
            popularity_score=self.popularity_score
        )

class AppointmentService(Base):
    __tablename__ = "appointment_service"
    
    service_id: Mapped[int] = mapped_column(Integer, ForeignKey("service.service_id", ondelete="CASCADE"), primary_key=True)
    appointment_id: Mapped[int] = mapped_column(Integer, ForeignKey("appointment.appointment_id", ondelete="CASCADE"), primary_key=True)
    
    '''
    AppointmentService class relationships
    '''

    # Each AppointmentService is linked to one Appointment
    service: Mapped["Service"] = relationship(back_populates="appointment_services", lazy="selectin")

    # Each AppointmentService is linked to one Service
    appointment: Mapped["Appointment"] = relationship(back_populates="appointment_services")


class Schedule(Base):
    __tablename__ = "schedule"
    
    schedule_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    barber_id: Mapped[int] = mapped_column(ForeignKey("barber.barber_id", ondelete="CASCADE"), nullable=False)
    date: Mapped[Date] = mapped_column(Date, nullable=False)
    is_working: Mapped[bool] = mapped_column(Boolean, default=True)

    # Unique constraint: A barber can have only one schedule per date
    __table_args__ = (UniqueConstraint("barber_id", "date", name="uq_barber_date"),)
    
    '''
    Schedule class relationships
    '''
    # Each schedule is assigned to a single Barber (Many-to-One)
    barber: Mapped["Barber"] = relationship(back_populates="schedules", lazy="selectin")

    # Each schedule links to multiple time slots (One-to-Many)
    time_slots: Mapped[list["TimeSlot"]] = relationship("TimeSlot", back_populates="schedule", cascade="all, delete, delete-orphan", lazy="selectin")

    def to_response_schema(self) -> ScheduleResponse:
        return ScheduleResponse(
            barber_id=self.barber_id,
            date=self.date,
            is_working=self.is_working,
            schedule_id=self.schedule_id,
            time_slots=[
                time_slot.to_response_schema() for time_slot in self.time_slots
            ],
            barber=self.barber.to_response_schema()
        )

class TimeSlot(Base):
    __tablename__ = "time_slots"

    slot_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    schedule_id: Mapped[int] = mapped_column(ForeignKey("schedule.schedule_id", ondelete="CASCADE"), nullable=False)
    start_time: Mapped[Time] = mapped_column(Time, nullable=False)
    end_time: Mapped[Time] = mapped_column(Time, nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    is_booked: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (UniqueConstraint("schedule_id", "start_time", "end_time", name="uq_schedule_time"),)

    '''
    TimeSlot class relationships
    '''
    #Multiple time slots link to one schedule (Many-to-One)
    schedule: Mapped["Schedule"] = relationship("Schedule", back_populates="time_slots", lazy="selectin")

    #Relationship to Appointment_TimeSlot (creates Many-to-Many with appointment)
    appointment_time_slots: Mapped[list["Appointment_TimeSlot"]] = relationship("Appointment_TimeSlot", back_populates="time_slot", cascade="all, delete, delete-orphan", lazy="selectin")
    
    def to_response_schema(self) -> TimeSlotChildResponse:
        return TimeSlotChildResponse(
            slot_id=self.slot_id,
            start_time=self.start_time,
            end_time=self.end_time,
            is_available=self.is_available,
            is_booked=self.is_booked
        )

class Appointment_TimeSlot(Base):
    __tablename__ = "appointment_time_slots"

    slot_id: Mapped[int] = mapped_column(Integer, ForeignKey("time_slots.slot_id", ondelete="CASCADE"), primary_key=True)
    appointment_id: Mapped[int] = mapped_column(Integer, ForeignKey("appointment.appointment_id", ondelete="CASCADE"), primary_key=True)

    '''
    Appointment_TimeSlot class relationships
    '''
    # Each Appointment_TimeSlot is linked to one TimeSlot
    time_slot: Mapped["TimeSlot"] = relationship(back_populates="appointment_time_slots", lazy="selectin")

    # Each Appointment_TimeSlot is linked to one TimeSlot
    appointment: Mapped["Appointment"] = relationship(back_populates="appointment_time_slots")

    


class Thread(Base):
    __tablename__ = "thread"
    
    thread_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    receivingUser: Mapped[int] = mapped_column(ForeignKey("user.user_id", ondelete="CASCADE"), nullable=False)
    sendingUser: Mapped[int] = mapped_column(ForeignKey("user.user_id", ondelete="CASCADE"), nullable=False)

    '''
    Thread class relationships
    '''
    # Each thread has one recieving User (Many-to-One)
    receiving_user: Mapped["User"] = relationship(foreign_keys=[receivingUser], back_populates="received_threads")

    # Each thread has one sender (Many-to-One)
    sending_user: Mapped["User"] = relationship(foreign_keys=[sendingUser], back_populates="sent_threads")

    # A thread can have multiple messages (One-To-Many)
    messages: Mapped[list["Message"]] = relationship(back_populates="thread")

class Message(Base):
    __tablename__ = "message"
    
    '''
    Message class relationships
    '''

    message_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    thread_id: Mapped[int] = mapped_column(ForeignKey("thread.thread_id", ondelete="CASCADE"), nullable=False)
    hasActiveMessage: Mapped[bool] = mapped_column(Boolean, default=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    timeStamp: Mapped[DateTime] = mapped_column(DateTime, default=func.current_timestamp())
    
    # Each message belongs to one thread (Many-To-One)
    thread: Mapped["Thread"] = relationship(back_populates="messages")
