-- Core "melt risk" business logic: a shipment is at risk if its transit delay
-- exceeds the product's melt tolerance window, or if refrigeration failed outright.
select
    s.shipment_id,
    s.product_id,
    p.product_name,
    s.warehouse_id,
    w.warehouse_name,
    w.region,
    s.ship_date,
    s.planned_transit_hours,
    s.actual_transit_hours,
    s.delay_hours,
    p.melt_tolerance_hours,
    s.refrigeration_failure,
    s.units_shipped,
    s.units_shipped * p.unit_cost as shipment_value,
    case
        when s.refrigeration_failure = 1 then 'CRITICAL - refrigeration failure'
        when s.delay_hours >= p.melt_tolerance_hours then 'HIGH - delay exceeds melt tolerance'
        when s.delay_hours >= (p.melt_tolerance_hours * 0.5) then 'MEDIUM - delay approaching melt tolerance'
        else 'LOW'
    end as melt_risk_level
from {{ ref('stg_shipments') }} s
join {{ ref('stg_products') }} p on s.product_id = p.product_id
join {{ ref('stg_warehouses') }} w on s.warehouse_id = w.warehouse_id
