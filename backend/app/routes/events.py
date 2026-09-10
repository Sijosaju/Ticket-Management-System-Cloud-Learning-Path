from datetime import date, time
from decimal import Decimal, InvalidOperation
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from ..auth import admin_required
from ..models import Event, TicketType, db

events_bp = Blueprint("events", __name__)

def error(message, status=400): return jsonify(error=message), status

def event_fields(event, data):
    required = ["title", "description", "category", "location", "event_date", "event_time"]
    if any(not data.get(k) for k in required): raise ValueError("Title, description, category, location, date, and time are required")
    event.title, event.description = data["title"].strip(), data["description"].strip()
    event.category, event.location = data["category"].strip(), data["location"].strip()
    event.event_date, event.event_time = date.fromisoformat(data["event_date"]), time.fromisoformat(data["event_time"])
    event.image_url, event.status = data.get("image_url") or None, data.get("status", "active")

@events_bp.get("/events")
def list_events():
    query = Event.query
    search, category = request.args.get("search", "").strip(), request.args.get("category", "").strip()
    if search: query = query.filter(Event.title.ilike(f"%{search}%"))
    if category: query = query.filter(Event.category == category)
    return jsonify(events=[e.public() for e in query.order_by(Event.event_date).all()])

@events_bp.get("/events/<int:event_id>")
def event_detail(event_id):
    event = db.session.get(Event, event_id)
    return (jsonify(event=event.public(True)), 200) if event else error("Event not found", 404)

@events_bp.post("/events")
@admin_required
def create_event():
    try:
        event = Event(); event_fields(event, request.get_json(silent=True) or {})
        db.session.add(event); db.session.commit(); return jsonify(event=event.public()), 201
    except (ValueError, TypeError) as exc: return error(str(exc))

@events_bp.put("/events/<int:event_id>")
@admin_required
def update_event(event_id):
    event = db.session.get(Event, event_id)
    if not event: return error("Event not found", 404)
    try:
        event_fields(event, request.get_json(silent=True) or {}); db.session.commit(); return jsonify(event=event.public())
    except (ValueError, TypeError) as exc: return error(str(exc))

@events_bp.delete("/events/<int:event_id>")
@admin_required
def cancel_event(event_id):
    event = db.session.get(Event, event_id)
    if not event: return error("Event not found", 404)
    event.status = "cancelled"; db.session.commit(); return "", 204

@events_bp.get("/events/<int:event_id>/tickets")
def tickets(event_id):
    event = db.session.get(Event, event_id)
    if not event: return error("Event not found", 404)
    return jsonify(ticket_types=[t.public() for t in event.ticket_types])

@events_bp.post("/events/<int:event_id>/tickets")
@admin_required
def create_ticket(event_id):
    if not db.session.get(Event, event_id): return error("Event not found", 404)
    data = request.get_json(silent=True) or {}
    try:
        qty = int(data.get("total_quantity")); price = Decimal(str(data.get("price")))
        if not data.get("name") or qty < 0 or price < 0: raise ValueError
        ticket = TicketType(event_id=event_id, name=data["name"].strip(), description=data.get("description", ""), price=price, total_quantity=qty, available_quantity=qty)
        db.session.add(ticket); db.session.commit(); return jsonify(ticket_type=ticket.public()), 201
    except (ValueError, TypeError, InvalidOperation): return error("Provide a ticket name, non-negative price, and non-negative quantity")

@events_bp.put("/events/<int:event_id>/tickets/<int:ticket_id>")
@admin_required
def update_ticket(event_id, ticket_id):
    ticket = db.session.get(TicketType, ticket_id)
    if not ticket or ticket.event_id != event_id: return error("Ticket type not found", 404)
    data = request.get_json(silent=True) or {}
    try:
        new_total = int(data.get("total_quantity", ticket.total_quantity))
        sold = ticket.total_quantity - ticket.available_quantity
        if new_total < sold: return error("Total quantity cannot be lower than tickets already sold")
        ticket.name, ticket.description = data.get("name", ticket.name), data.get("description", ticket.description)
        ticket.price, ticket.total_quantity, ticket.available_quantity = Decimal(str(data.get("price", ticket.price))), new_total, new_total - sold
        db.session.commit(); return jsonify(ticket_type=ticket.public())
    except (ValueError, TypeError, InvalidOperation): return error("Invalid ticket values")
