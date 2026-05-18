from flask import request

from app import db
from app.api import bp
from app.etl import queries


@bp.route("/daily-auction-results", methods=["GET"])
def get_daily_auction_results():
    start = request.args.get("start")
    length = request.args.get("length")
    sort = request.args.get("sort")
    search = request.args.get("search")

    data_query = queries.paginated_auction_unit_results(start, length, sort, search)
    total_query = queries.habitat_results(search)

    return {
        "data": [
            result.to_dict() for result in db.session.execute(data_query).scalars()
        ],
        "total": db.session.scalar(total_query),
    }
