select
    warehouse_id,
    warehouse_name,
    region
from {{ source('raw', 'warehouses') }}
