import sqlalchemy as sa

from app.models import AuctionUnitResult

HABITAT_PARTICIPANT = "HABITAT ENERGY LIMITED"
HABITAT_SERVICE_TYPE = "Response"
DEFAULT_START = 0
DEFAULT_LENGTH = 20
DEFAULT_SORT_ORDER = (
    AuctionUnitResult.delivery_start_utc.asc(),
    AuctionUnitResult.id.asc(),
)

SORT_COLUMNS = {
    "id": AuctionUnitResult.id,
    "date": AuctionUnitResult.delivery_start_utc,
    "delivery_start": AuctionUnitResult.delivery_start_utc,
    "delivery_start_utc": AuctionUnitResult.delivery_start_utc,
    "participant": AuctionUnitResult.registered_auction_participant,
    "registered_auction_participant": AuctionUnitResult.registered_auction_participant,
    "unit": AuctionUnitResult.auction_unit,
    "auction_unit": AuctionUnitResult.auction_unit,
    "product": AuctionUnitResult.auction_product,
    "auction_product": AuctionUnitResult.auction_product,
    "quantity": AuctionUnitResult.executed_quantity_mw,
    "executed_quantity_mw": AuctionUnitResult.executed_quantity_mw,
    "clearing_price": AuctionUnitResult.clearing_price_gbp_per_mw_h,
    "clearing_price_gbp_per_mw_h": AuctionUnitResult.clearing_price_gbp_per_mw_h,
}

SEARCH_COLUMNS = (
    AuctionUnitResult.auction_unit,
    AuctionUnitResult.auction_product,
    AuctionUnitResult.technology_type,
    AuctionUnitResult.post_code,
    AuctionUnitResult.unit_result_id,
)


def _with_habitat_filters(q, search):
    q = q.where(
        AuctionUnitResult.registered_auction_participant == HABITAT_PARTICIPANT,
        AuctionUnitResult.service_type == HABITAT_SERVICE_TYPE,
    )
    search = (search or "").strip()
    if not search:
        return q

    pattern = f"%{search}%"
    return q.where(sa.or_(*(column.ilike(pattern) for column in SEARCH_COLUMNS)))


def _coerce_int(value, default, minimum=None):
    try:
        value = int(value)
    except (TypeError, ValueError):
        return default

    if minimum is not None and value < minimum:
        return default
    return value


def _sort_order(sort):
    if not sort:
        return DEFAULT_SORT_ORDER

    order = []
    for sort_item in sort.split(","):
        sort_item = sort_item.strip()
        if not sort_item:
            continue

        direction = sort_item[0]
        name = sort_item[1:] if direction in ("+", "-") else sort_item
        column = SORT_COLUMNS.get(name)
        if column is None:
            continue

        if direction == "-":
            column = column.desc()
        order.append(column)

    return order or DEFAULT_SORT_ORDER


def paginated_auction_unit_results(start, length, sort, search):
    start = _coerce_int(start, DEFAULT_START, minimum=0)
    length = _coerce_int(length, DEFAULT_LENGTH, minimum=1)
    q = sa.select(AuctionUnitResult)
    q = _with_habitat_filters(q, search)
    return q.order_by(*_sort_order(sort)).offset(start).limit(length)


def habitat_results(search):
    q = sa.select(sa.func.count(AuctionUnitResult.id))
    return _with_habitat_filters(q, search)
