-- Inventory health: combines stock-out risk (below reorder point) with
-- cold-chain risk (freezer running warm at the storage hub itself).
select
    i.product_id,
    p.product_name,
    i.warehouse_id,
    w.warehouse_name,
    w.region,
    i.stock_on_hand,
    i.reorder_point,
    i.freezer_temp_c,
    i.is_freezer_warm,
    i.snapshot_date,
    case
        when i.stock_on_hand < i.reorder_point then true else false
    end as is_understocked,
    case
        when i.is_freezer_warm and i.stock_on_hand > 0 then 'CRITICAL - stock sitting in warm freezer'
        when i.stock_on_hand < i.reorder_point then 'LOW STOCK'
        else 'OK'
    end as inventory_status
from {{ ref('stg_inventory') }} i
join {{ ref('stg_products') }} p on i.product_id = p.product_id
join {{ ref('stg_warehouses') }} w on i.warehouse_id = w.warehouse_id
