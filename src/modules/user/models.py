from decimal import Decimal
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship
)

from sqlalchemy import (
    DECIMAL,
    String,
    Boolean,
    ForeignKey,
    Float,
    Time,
    DateTime,
    Integer,
    Enum,
    Text
)

from sqlalchemy.sql import func

import enum

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


class Barber(Base):
    __tablename__ = "barber"
    
    barber_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.user_id", ondelete="CASCADE"), nullable=False, unique=True)
    
    '''
    Barber class relationships
    '''

    # Barber is linked to a single user (as specified by 'uselist = false' in User table above. One-to-One)
    user: Mapped["User"] = relationship(back_populates="barber")

    # Barber can have multiple Appointments (One-to-Many)
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="barber")

    # A Barber can have multiple Schedules (One-to-Many)
    schedules: Mapped[list["Schedule"]] = relationship(back_populates="barber")


class Appointment(Base):
    __tablename__ = "appointment"
    
    appointment_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.user_id", ondelete="CASCADE"), nullable=False)
    barber_id: Mapped[int] = mapped_column(Integer, ForeignKey("barber.barber_id", ondelete="CASCADE"), nullable=False)
    status: Mapped[AppointmentStatus] = mapped_column(Enum(AppointmentStatus), nullable=False)
    
    '''
    Appointment class relationships
    '''

    # Each appointment is linked to one User (who booked it) - (Many-to-One)
    user: Mapped["User"] = relationship(back_populates="appointments")

    # Each appointment is assigned to one Barber (Many-to-One)
    barber: Mapped["Barber"] = relationship(back_populates="appointments")

    # An Appointment can have multiple AppointmentService records ()
    services: Mapped[list["AppointmentService"]] = relationship(back_populates="appointment")

    # One-to-Many - Appointment can have more than one schedule
    schedule: Mapped[list["Schedule"]] = relationship(back_populates="appointment")


class Service(Base):
    __tablename__ = "service"
    
    service_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    duration: Mapped[Time] = mapped_column(Time, nullable=False)
    price: Mapped[Float] = mapped_column(Float(5, 2), nullable=False)
    
    '''
    Service class relationships
    '''

    # A service can be linked to multiple AppointmentService records (One-to-Many)
    appointment_services: Mapped[list["AppointmentService"]] = relationship(back_populates="service")


class AppointmentService(Base):
    __tablename__ = "appointment_service"
    
    service_id: Mapped[int] = mapped_column(Integer, ForeignKey("service.service_id", ondelete="CASCADE"), primary_key=True)
    appointment_id: Mapped[int] = mapped_column(Integer, ForeignKey("appointment.appointment_id", ondelete="CASCADE"), primary_key=True)
    
    '''
    AppointmentService class relationships
    '''

    # Each AppointmentService is linked to one Appointment
    service: Mapped["Service"] = relationship(back_populates="appointment_services")

    # Each AppointmentService is linked to one Service
    appointment: Mapped["Appointment"] = relationship(back_populates="services")


class Schedule(Base):
    __tablename__ = "schedule"
    
    schedule_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    barber_id: Mapped[int] = mapped_column(ForeignKey("barber.barber_id", ondelete="CASCADE"), nullable=False)
    appointment_id: Mapped[int] = mapped_column(ForeignKey("appointment.appointment_id", ondelete="SET NULL"))
    date: Mapped[str] = mapped_column(String(10), nullable=False)
    startTime: Mapped[Time] = mapped_column(Time, nullable=False)
    endTime: Mapped[Time] = mapped_column(Time, nullable=False)
    
    '''
    Schedule class relationships
    '''

    # Each schedule is assigned to a single Barber (Many-to-One)
    barber: Mapped["Barber"] = relationship(back_populates="schedules")

    # Each schedule links to one appointment (Many-to-One)
    appointment: Mapped["Appointment"] = relationship(back_populates="schedule")

class Thread(Base):
    __tablename__ = "thread"
    
    '''
    Thread class relationships
    '''
    thread_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    receivingUser: Mapped[int] = mapped_column(ForeignKey("user.user_id", ondelete="CASCADE"), nullable=False)
    sendingUser: Mapped[int] = mapped_column(ForeignKey("user.user_id", ondelete="CASCADE"), nullable=False)
    
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
    hasActiveMessage: Mapped[bool] = mapped_column(Boolean)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    timeStamp: Mapped[DateTime] = mapped_column(DateTime, default=func.current_timestamp())
    
    # Each message belongs to one thread (Many-To-One)
    thread: Mapped["Thread"] = relationship(back_populates="messages")
