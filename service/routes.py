######################################################################
# Product Store Service with UI
######################################################################
from flask import jsonify, request, abort, url_for
from service.models import Product, Category
from service.common import status
from . import app


######################################################################
# HEALTH CHECK
######################################################################
@app.route("/health")
def healthcheck():
    return jsonify(status=200, message="OK"), status.HTTP_200_OK


######################################################################
# HOME PAGE
######################################################################
@app.route("/")
def index():
    return app.send_static_file("index.html")


######################################################################
# UTILITY
######################################################################
def check_content_type(content_type):
    if "Content-Type" not in request.headers:
        abort(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    if request.headers["Content-Type"] != content_type:
        abort(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)


######################################################################
# CREATE PRODUCT
######################################################################
@app.route("/products", methods=["POST"])
def create_products():
    check_content_type("application/json")

    product = Product()
    try:
        product.deserialize(request.get_json())
        product.create()
    except Exception:
        abort(status.HTTP_400_BAD_REQUEST)

    location_url = url_for("get_products", product_id=product.id, _external=True)
    return jsonify(product.serialize()), status.HTTP_201_CREATED, {"Location": location_url}


######################################################################
# LIST PRODUCTS (WITH FILTER)
######################################################################
@app.route("/products", methods=["GET"])
def list_products():
    name = request.args.get("name")
    category = request.args.get("category")
    available = request.args.get("available")

    if name:
        products = Product.find_by_name(name)
    elif category:
        try:
            cat = Category[category]
            products = Product.find_by_category(cat)
        except KeyError:
            abort(status.HTTP_400_BAD_REQUEST)
    elif available:
        avail = available.lower() == "true"
        products = Product.find_by_availability(avail)
    else:
        products = Product.all()

    results = [product.serialize() for product in products]
    return jsonify(results), status.HTTP_200_OK


######################################################################
# READ PRODUCT
######################################################################
@app.route("/products/<int:product_id>", methods=["GET"])
def get_products(product_id):
    product = Product.find(product_id)
    if not product:
        abort(status.HTTP_404_NOT_FOUND, f"Product with id '{product_id}' was not found.")
    return jsonify(product.serialize()), status.HTTP_200_OK


######################################################################
# UPDATE PRODUCT
######################################################################
@app.route("/products/<int:product_id>", methods=["PUT"])
def update_products(product_id):
    product = Product.find(product_id)
    if not product:
        abort(status.HTTP_404_NOT_FOUND)

    try:
        product.deserialize(request.get_json())
        product.update()
    except Exception:
        abort(status.HTTP_400_BAD_REQUEST)

    return jsonify(product.serialize()), status.HTTP_200_OK


######################################################################
# DELETE PRODUCT
######################################################################
@app.route("/products/<int:product_id>", methods=["DELETE"])
def delete_products(product_id):
    product = Product.find(product_id)
    if not product:
        abort(status.HTTP_404_NOT_FOUND)

    product.delete()
    return "", status.HTTP_204_NO_CONTENT