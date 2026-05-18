from app.api import bp


@bp.route("/participants", methods=["GET"])
def get_participants():
    """ """
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 100)
    return Researcher.to_collection_dict(
        sa.select(Researcher), page, per_page, "src.api.get_researchers"
    )
