from flask import render_template, request
from app import db
from app.main import bp


@bp.route("/", methods=["GET"])
@bp.route("/index", methods=["GET"])
def index():
    return render_template("index.html", messages=[])


@bp.route("/api/orders")
def get_habitat_results():
    start = request.args.get("start")
    length = request.args.get("length")
    sort = request.args.get("sort")
    search = request.args.get("search")

    data_query = queries.paginated_orders(start, length, sort, search)
    total_query = queries.total_orders(search)

    orders = db.session.execute(data_query)
    data = [{**o[0].to_dict(), "total": o[1]} for o in orders]
    return {
        "data": data,
        "total": db.session.scalar(total_query),
    }
