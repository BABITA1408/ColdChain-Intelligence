select
    product_id,
    product_name,
    format,
    shelf_life_days_frozen,
    melt_tolerance_hours,
    unit_cost
from {{ source('raw', 'products') }}
