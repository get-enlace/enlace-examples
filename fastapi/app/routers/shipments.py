"""Shipment resource endpoints - using SQLAlchemy ORM."""

from datetime import datetime

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..dependencies import get_current_carrier_key
from ..errors import conflict, not_found
from ..models import Order, Shipment
from ..schemas import ErrorResponse, Shipment as ShipmentSchema
from ..schemas import ShipmentStatusRequest

router = APIRouter(tags=["shipments"])


@router.get(
    "/shipments/{tracking_number}",
    response_model=ShipmentSchema,
    responses={
        404: {"model": ErrorResponse},
    },
)
async def get_shipment(
    tracking_number: str,
    db: AsyncSession = Depends(get_db),
) -> ShipmentSchema:
    """Get a shipment by tracking number (public — tracking number is the secret)."""
    result = await db.execute(
        select(Shipment).where(Shipment.tracking_number == tracking_number)
    )
    shipment = result.scalars().first()

    if not shipment:
        raise not_found("Shipment", tracking_number)

    return ShipmentSchema(
        id=shipment.id,
        orderId=shipment.order_id,
        trackingNumber=shipment.tracking_number,
        carrier=shipment.carrier,
        status=shipment.status,
        createdAt=shipment.created_at,
    )


@router.put(
    "/shipments/{tracking_number}/status",
    response_model=ShipmentSchema,
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
    db: AsyncSession = Depends(get_db),
) -> ShipmentSchema:
    """Update a shipment's status (carrier API key only).

    Only accepts 'delivered' as a new status (from 'in_transit').
    Cascades the parent order to 'delivered'.
    """
    result = await db.execute(
        select(Shipment).where(Shipment.tracking_number == tracking_number)
    )
    shipment = result.scalars().first()

    if not shipment:
        raise not_found("Shipment", tracking_number)

    if shipment.status != "in_transit":
        raise conflict(f"Cannot update a shipment in '{shipment.status}' status (must be 'in_transit')")

    if req.status != "delivered":
        raise conflict(f"Invalid status transition to '{req.status}' (only 'delivered' is valid from 'in_transit')")

    # Update shipment
    shipment.status = req.status

    # Cascade order to 'delivered'
    result = await db.execute(
        select(Order).where(Order.id == shipment.order_id)
    )
    order = result.scalars().first()
    if order:
        order.status = "delivered"

    await db.commit()

    return ShipmentSchema(
        id=shipment.id,
        orderId=shipment.order_id,
        trackingNumber=tracking_number,
        carrier=shipment.carrier,
        status=req.status,
        createdAt=shipment.created_at,
    )
