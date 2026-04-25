"""
Product API Service Test Suite
"""
import os
import logging
from decimal import Decimal
from unittest import TestCase
from service import app
from service.common import status
from service.models import db, init_db, Product
from tests.factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)
BASE_URL = "/products"


class TestProductRoutes(TestCase):

    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        db.session.close()

    def setUp(self):
        self.client = app.test_client()
        db.session.query(Product).delete()
        db.session.commit()

    def tearDown(self):
        db.session.remove()

    ############################################################
    # Utility
    ############################################################
    def _create_products(self, count=1):
        products = []
        for _ in range(count):
            product = ProductFactory()
            response = self.client.post(BASE_URL, json=product.serialize())
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            data = response.get_json()
            product.id = data["id"]
            products.append(product)
        return products

    ############################################################
    # BASIC
    ############################################################
    def test_index(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    ############################################################
    # ERROR HANDLER (BOOST COVERAGE)
    ############################################################
    def test_404_handler(self):
        response = self.client.get("/random-url")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_405_handler(self):
        response = self.client.put("/health")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    ############################################################
    # CREATE
    ############################################################
    def test_create_product(self):
        product = ProductFactory()
        response = self.client.post(BASE_URL, json=product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = response.get_json()
        self.assertEqual(data["name"], product.name)
        self.assertEqual(Decimal(data["price"]), product.price)

    def test_create_product_with_no_name(self):
        product = ProductFactory()
        data = product.serialize()
        del data["name"]

        response = self.client.post(BASE_URL, json=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_product_no_content_type(self):
        response = self.client.post(BASE_URL, data="bad data")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_create_product_wrong_content_type(self):
        response = self.client.post(BASE_URL, data={}, content_type="plain/text")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_create_product_missing_content_type_header(self):
        response = self.client.post(BASE_URL, data='{}', headers={})
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_create_product_empty_json(self):
        response = self.client.post(BASE_URL, json={})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_product_invalid_type(self):
        response = self.client.post(BASE_URL, json={
            "name": "Test",
            "description": "Test",
            "price": "10.0",
            "available": "yes",  # salah
            "category": "FOOD"
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_product_invalid_category(self):
        response = self.client.post(BASE_URL, json={
            "name": "Test",
            "description": "Test",
            "price": "10.0",
            "available": True,
            "category": "INVALID"
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_product_bad_body(self):
        response = self.client.post(
            BASE_URL,
            data="not json",
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    ############################################################
    # READ
    ############################################################
    def test_get_product(self):
        product = self._create_products(1)[0]
        response = self.client.get(f"{BASE_URL}/{product.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_product_not_found(self):
        response = self.client.get(f"{BASE_URL}/0")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    ############################################################
    # UPDATE
    ############################################################
    def test_update_product(self):
        product = self._create_products(1)[0]
        product.name = "Updated Name"

        response = self.client.put(
            f"{BASE_URL}/{product.id}",
            json=product.serialize()
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_product_not_found(self):
        response = self.client.put(f"{BASE_URL}/0", json={})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_product_invalid_data(self):
        product = self._create_products(1)[0]

        response = self.client.put(
            f"{BASE_URL}/{product.id}",
            json={"available": "yes"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_bad_json(self):
        product = self._create_products(1)[0]

        response = self.client.put(
            f"{BASE_URL}/{product.id}",
            data="not json",
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    ############################################################
    # DELETE
    ############################################################
    def test_delete_product(self):
        product = self._create_products(1)[0]

        response = self.client.delete(f"{BASE_URL}/{product.id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_product_not_found(self):
        response = self.client.delete(f"{BASE_URL}/0")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    ############################################################
    # LIST
    ############################################################
    def test_list_all_products(self):
        self._create_products(5)
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.get_json()
        self.assertEqual(len(data), 5)

    def test_list_products_empty(self):
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.get_json(), [])

    def test_list_by_name(self):
        products = self._create_products(5)
        name = products[0].name

        response = self.client.get(f"{BASE_URL}?name={name}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_by_category(self):
        products = self._create_products(5)
        category = products[0].category.name

        response = self.client.get(f"{BASE_URL}?category={category}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_invalid_category(self):
        response = self.client.get(f"{BASE_URL}?category=INVALID")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_by_availability(self):
        products = self._create_products(5)
        available = str(products[0].available).lower()

        response = self.client.get(f"{BASE_URL}?available={available}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)