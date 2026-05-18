REGISTERED_AUCTION_PARTICIPANT = "registeredAuctionParticipant"
AUCTION_UNIT = "auctionUnit"
SERVICE_TYPE = "serviceType"
AUCTION_PRODUCT = "auctionProduct"
EXECUTED_QUANTITY = "executedQuantity"
CLEARING_PRICE = "clearingPrice"
DELIVERY_START = "deliveryStart"
DELIVERY_END = "deliveryEnd"
TECHNOLOGY_TYPE = "technologyType"
POST_CODE = "postCode"
UNIT_RESULT_ID = "unitResultID"

UNIT_RESULT_FIELDS = (
    REGISTERED_AUCTION_PARTICIPANT,
    AUCTION_UNIT,
    SERVICE_TYPE,
    AUCTION_PRODUCT,
    EXECUTED_QUANTITY,
    CLEARING_PRICE,
    DELIVERY_START,
    DELIVERY_END,
    TECHNOLOGY_TYPE,
    POST_CODE,
    UNIT_RESULT_ID,
)

UNIT_RESULT_FIELD_MAP = {
    REGISTERED_AUCTION_PARTICIPANT: "registered_auction_participant",
    AUCTION_UNIT: "auction_unit",
    SERVICE_TYPE: "service_type",
    AUCTION_PRODUCT: "auction_product",
    EXECUTED_QUANTITY: "executed_quantity_mw",
    CLEARING_PRICE: "clearing_price_gbp_per_mw_h",
    DELIVERY_START: "delivery_start_utc",
    DELIVERY_END: "delivery_end_utc",
    TECHNOLOGY_TYPE: "technology_type",
    POST_CODE: "post_code",
    UNIT_RESULT_ID: "unit_result_id",
}
