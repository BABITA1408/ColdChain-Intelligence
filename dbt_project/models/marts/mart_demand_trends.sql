-- Daily demand aggregated per product/warehouse - the base table the agent's
-- forecast tool queries to compute recent trends and simple moving averages.
select
    order_date,
    product_id,
    warehouse_id,
    sum(units_ordered) as total_units_ordered,
    sum(order_value) as total_order_value
from {{ ref('stg_orders') }}
group by 1, 2, 3
