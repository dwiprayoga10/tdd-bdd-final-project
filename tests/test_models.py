# Copyright 2016, 2023 John J. Rofrano.

"""
Test cases for Product Model
"""
import os
import logging
import unittest
from decimal import Decimal
from service.models import Product, Category, db
from service import app
from tests.factories import ProductFactory

# ✅ gunakan env + fallback ke port 5433 (yang kita pakai docker)
DATABASE_URI = os.getenv(
    "DATABASE_URI",
    "postgresql://postgres:postgres@localhost:5433/postgres"
)


######################################################################
#  P R O D U C T   M O D E L   T E S T   C A S E S
######################################################################
class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        db.session.close()

    def setUp(self):
        # bersihkan database sebelum tiap test
        db.session.query(Product).delete()
        db.session.commit()

    def tearDown(self):
        db.session.remove()

    ##################################################################
    # CREATE
    ##################################################################
    def test_create_a_product(self):
        product = Product(
            name="Fedora",
            description="A red hat",
            price=12.50,
            available=True,
            category=Category.CLOTHS,
        )
        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertIsNotNone(product)
        self.assertEqual(product.id, None)

    ##################################################################
    # ADD
    ##################################################################
    def test_add_a_product(self):
        self.assertEqual(Product.all(), [])

        product = ProductFactory()
        product.id = None
        product.create()

        self.assertIsNotNone(product.id)

        products = Product.all()
        self.assertEqual(len(products), 1)

        new_product = products[0]
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(Decimal(new_product.price), product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    ##################################################################
    # READ
    ##################################################################
    def test_read_a_product(self):
        product = ProductFactory()
        product.id = None
        product.create()

        found = Product.find(product.id)

        self.assertIsNotNone(found)
        self.assertEqual(found.id, product.id)
        self.assertEqual(found.name, product.name)
        self.assertEqual(found.description, product.description)
        self.assertEqual(found.price, product.price)

    ##################################################################
    # UPDATE
    ##################################################################
    def test_update_a_product(self):
        product = ProductFactory()
        product.id = None
        product.create()

        original_id = product.id
        product.description = "updated"
        product.update()

        self.assertEqual(product.id, original_id)
        self.assertEqual(product.description, "updated")

        products = Product.all()
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].description, "updated")

    ##################################################################
    # DELETE
    ##################################################################
    def test_delete_a_product(self):
        product = ProductFactory()
        product.create()

        self.assertEqual(len(Product.all()), 1)

        product.delete()
        self.assertEqual(len(Product.all()), 0)

    ##################################################################
    # LIST ALL
    ##################################################################
    def test_list_all_products(self):
        self.assertEqual(Product.all(), [])

        for _ in range(5):
            ProductFactory().create()

        self.assertEqual(len(Product.all()), 5)

    ##################################################################
    # FIND BY NAME
    ##################################################################
    def test_find_by_name(self):
        products = ProductFactory.create_batch(5)

        for product in products:
            product.create()

        name = products[0].name
        count = len([p for p in products if p.name == name])

        found = Product.find_by_name(name)

        self.assertEqual(found.count(), count)
        for product in found:
            self.assertEqual(product.name, name)

    ##################################################################
    # FIND BY AVAILABILITY
    ##################################################################
    def test_find_by_availability(self):
        products = ProductFactory.create_batch(10)

        for product in products:
            product.create()

        available = products[0].available
        count = len([p for p in products if p.available == available])

        found = Product.find_by_availability(available)

        self.assertEqual(found.count(), count)
        for product in found:
            self.assertEqual(product.available, available)

    ##################################################################
    # FIND BY CATEGORY
    ##################################################################
    def test_find_by_category(self):
        products = ProductFactory.create_batch(10)

        for product in products:
            product.create()

        category = products[0].category
        count = len([p for p in products if p.category == category])

        found = Product.find_by_category(category)

        self.assertEqual(found.count(), count)
        for product in found:
            self.assertEqual(product.category, category)