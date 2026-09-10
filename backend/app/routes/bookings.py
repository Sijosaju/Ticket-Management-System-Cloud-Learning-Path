from decimal import Decimal
from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from ..auth import admin_required
from ..models import Booking, BookingItem, Event, TicketType, User, db

bookings_bp = Blueprint("bookings", __name__)
def error(message, status=400): return jsonify(error=message), status
def current_user_id(): return int(get_jwt_identity())

@bookings_bp.post("")
@jwt_required()
def create_booking():
    data = request.get_json(silent=True) or {}
    event_id, requested = data.get("event_id"), data.get("items", [])
    if not event_id or not requested: return error("event_id and at least one ticket item are required")
    try:
        with db.session.begin():
            event = db.session.get(Event, int(event_id))
            if not event or event.status != "active": return error("This event is unavailable", 404)
            ticket_ids = [int(item["ticket_type_id"]) for item in requested]
            quantities = [int(item["quantity"]) for item in requested]
            if any(qty <= 0 for qty in quantities) or len(set(ticket_ids)) != len(ticket_ids): return error("Ticket quantities must be positive and ticket types unique")
            # Row locks prevent simultaneous bookings from overselling tickets on MySQL/InnoDB.
            tickets = {t.id: t for t in TicketType.query.filter(TicketType.id.in_(ticket_ids), TicketType.event_id == event.id).with_for_update().all()}
            if len(tickets) != len(ticket_ids): return error("Invalid ticket type for this event")
            for ticket_id, quantity in zip(ticket_ids, quantities):
                if tickets[ticket_id].available_quantity < quantity: return error(f"Not enough {tickets[ticket_id].name} tickets available", 409)
            total = sum(tickets[i].price * q for i, q in zip(ticket_ids, quantities))
            booking = Booking(user_id=current_user_id(), event_id=event.id, total_amount=total)
            db.session.add(booking); db.session.flush()
            for ticket_id, quantity in zip(ticket_ids, quantities):
                ticket = tickets[ticket_id]; ticket.available_quantity -= quantity
                db.session.add(BookingItem(booking_id=booking.id, ticket_type_id=ticket.id, quantity=quantity, unit_price=ticket.price, subtotal=ticket.price * quantity))
        current_app.logger.info("Booking created: booking_id=%s user_id=%s", booking.id, current_user_id())
        return jsonify(booking=booking.public()), 201
    except (KeyError, TypeError, ValueError):
        db.session.rollback(); return error("Invalid booking payload")

@bookings_bp.get("")
@jwt_required()
def list_bookings():
    user = db.session.get(User, current_user_id())
    query = Booking.query.order_by(Booking.created_at.desc())
    if user.role != "admin": query = query.filter_by(user_id=user.id)
    return jsonify(bookings=[booking.public() for booking in query.all()])

@bookings_bp.get("/<int:booking_id>")
@jwt_required()
def booking_detail(booking_id):
    booking, user = db.session.get(Booking, booking_id), db.session.get(User, current_user_id())
    if not booking: return error("Booking not found", 404)
    if booking.user_id != user.id and user.role != "admin": return error("Not authorized", 403)
    return jsonify(booking=booking.public())

@bookings_bp.post("/<int:booking_id>/cancel")
@jwt_required()
def cancel_booking(booking_id):
    with db.session.begin():
        booking = Booking.query.filter_by(id=booking_id).with_for_update().one_or_none()
        if not booking: return error("Booking not found", 404)
        user = db.session.get(User, current_user_id())
        if booking.user_id != user.id and user.role != "admin": return error("Not authorized", 403)
        if booking.status == "cancelled": return error("Booking is already cancelled", 409)
        for item in booking.items:
            ticket = TicketType.query.filter_by(id=item.ticket_type_id).with_for_update().one()
            ticket.available_quantity += item.quantity
        booking.status = "cancelled"
    current_app.logger.info("Booking cancelled: booking_id=%s user_id=%s", booking_id, user.id)
    return jsonify(booking=booking.public())
