from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    bookings = db.relationship("Booking", back_populates="user")

    def public(self): return {"id": self.id, "name": self.name, "email": self.email, "role": self.role}


class Event(db.Model):
    __tablename__ = "events"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    event_date = db.Column(db.Date, nullable=False)
    event_time = db.Column(db.Time, nullable=False)
    image_url = db.Column(db.String(500))
    status = db.Column(db.String(20), nullable=False, default="active")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    ticket_types = db.relationship("TicketType", back_populates="event", cascade="all, delete-orphan")

    def public(self, include_tickets=False):
        data = {"id": self.id, "title": self.title, "description": self.description, "category": self.category,
                "location": self.location, "event_date": self.event_date.isoformat(), "event_time": self.event_time.strftime("%H:%M"),
                "image_url": self.image_url, "status": self.status}
        if include_tickets: data["ticket_types"] = [ticket.public() for ticket in self.ticket_types]
        return data


class TicketType(db.Model):
    __tablename__ = "ticket_types"
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    total_quantity = db.Column(db.Integer, nullable=False)
    available_quantity = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    event = db.relationship("Event", back_populates="ticket_types")

    def public(self): return {"id": self.id, "name": self.name, "description": self.description, "price": float(self.price), "total_quantity": self.total_quantity, "available_quantity": self.available_quantity}


class Booking(db.Model):
    __tablename__ = "bookings"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False, index=True)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="confirmed")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user = db.relationship("User", back_populates="bookings")
    event = db.relationship("Event")
    items = db.relationship("BookingItem", back_populates="booking", cascade="all, delete-orphan")

    def public(self): return {"id": self.id, "event": self.event.public(), "user_name": self.user.name, "user_email": self.user.email, "total_amount": float(self.total_amount), "status": self.status, "created_at": self.created_at.isoformat(), "items": [item.public() for item in self.items]}


class BookingItem(db.Model):
    __tablename__ = "booking_items"
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"), nullable=False)
    ticket_type_id = db.Column(db.Integer, db.ForeignKey("ticket_types.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    booking = db.relationship("Booking", back_populates="items")
    ticket_type = db.relationship("TicketType")

    def public(self): return {"ticket_type": self.ticket_type.name, "ticket_type_id": self.ticket_type_id, "quantity": self.quantity, "unit_price": float(self.unit_price), "subtotal": float(self.subtotal)}
