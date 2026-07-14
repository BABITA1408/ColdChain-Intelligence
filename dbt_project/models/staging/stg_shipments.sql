select
    shipment_id,
    product_id,
    warehouse_id,
    cast(ship_date as date) as ship_date,
    planned_transit_hours,
    actual_transit_hours,
    actual_transit_hours - planned_transit_hours as delay_hours,
    refrigeration_failure,
    units_shipped
from {{ source('raw', 'shipments') }}
