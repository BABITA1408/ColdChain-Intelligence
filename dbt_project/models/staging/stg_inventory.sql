select
    product_id,
    warehouse_id,
    stock_on_hand,
    reorder_point,
    freezer_temp_c,
    cast(snapshot_date as date) as snapshot_date,
    case when freezer_temp_c > -18 then true else false end as is_freezer_warm
from {{ source('raw', 'inventory') }}
