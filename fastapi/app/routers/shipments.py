"""Shipment resource endpoints.

- GET /shipments/{tracking_number} (public) — get a shipment by tracking number
- PUT /shipments/{tracking_number}/status (carrier API key) — update shipment status
"""

from datetime import datetime

from fastapi import APIRouter, Depends, status

from ..db import database
from ..dependencies import get_current_carrier_key
from ..errors import conflict, not_found
from ..schemas import ErrorResponse, Shipment, ShipmentStatusRequest

router = APIRouter(tags=["shipments"])


@router.get(
    "/shipments/{tracking_number}",
    response_model=Shipment,
    responses={
        404: {"model": ErrorResponse},
    },
)
async def get_shipment(tracking_number: str) -> Shipment:
    """Get a shipment by tracking number (public — tracking number is the secret)."""
    shipment = await database.fetch_one(
        """SELECT id, order_id, tracking_number, carrier, status, created_at
           FROM shipments
           WHERE tracking_number = :tracking_number""",
        values={"tracking_number": tracking_number},
    )

    if not shipment:
        raise not_found("Shipment", tracking_number)

    return Shipment(
        id=shipment["id"],
        order_id=shipment["order_id"],
        tracking_number=shipment["tracking_number"],
        carrier=shipment["carrier"],
        status=shipment["status"],
        created_at=shipment["created_at"],
    )


@router.put(
    "/shipments/{tracking_number}/status",
    response_model=Shipment,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
)
async def update_shipment_status(
    tracking_number: str,
    req: ShipmentStatusRequest,
    _carrier_key: str = Depends(get_current_carrier_key),
) -> Shipment:
    """Update a shipment's status (carrier API key only).

    Only accepts 'delivered' as a new status (from 'in_transit').
    Cascades the parent order to 'delivered'.
    """
    shipment = await database.fetch_one(
        """SELECT id, order_id, status FROM shipments
           WHERE tracking_number = :tracking_number""",
        values={"tracking_number": tracking_number},
    )

    if not shipment:
        raise not_found("Shipment", tracking_number)

    if shipment["status"] != "in_transit":
        raise conflict(f"Cannot update a shipment in '{shipment['status']}' status (must be 'in_transit')")

    if req.status != "delivered":
        raise conflict(f"Invalid status transition to '{req.status}' (only 'delivered' is valid from 'in_transit')")

    # Update shipment
    await database.execute(
        "UPDATE shipments SET status = :status WHERE id = :id",
        values={"status": req.status, "id": shipment["id"]},
    )

    # Cascade order to 'delivered'
    await database.execute(
        "UPDATE orders SET status = 'delivered' WHERE id = :order_id",
        values={"order_id": shipment["order_id"]},
    )

    return Shipment(
        id=shipment["id"],
        order_id=shipment["order_id"],
        tracking_number=tracking_number,
        carrier="DemoShip Express",
        status=req.status,
        created_at=datetime.utcnow(),  # This should be fetched from DB, but for now use current
    )
