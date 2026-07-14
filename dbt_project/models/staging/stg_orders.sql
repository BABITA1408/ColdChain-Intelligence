select
    cast(order_date as date) as order_date,
    product_id,
    warehouse_id,
    units_ordered,
    unit_cost,
    units_ordered * unit_cost as order_value
from {{ source('raw', 'orders') }}
