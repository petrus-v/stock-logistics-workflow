# Copyright 2023-2024 Foodles (https://www.foodles.co/).
# @author Pierre Verkest <pierreverkest84@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo.tests.common import SavepointCase


class TestPlannedExpiryDateMode(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_id = cls.env["res.partner"].create({"name": "Supplier"})
        cls.product1 = cls.env["product.product"].create(
            {
                "name": "Test Product 1",
                "type": "product",
                "default_code": "PROD1",
                "expiration_time": 1,
                "tracking": "lot",
                "use_expiration_date": True,
                "product_planned_expiry_date_mode": "inherited_from_category",
            }
        )
        cls.product1.categ_id.planned_expiry_date_mode = "exact"

    def test_compute_planned_expiry_date_mode_inherited(self):
        self.assertEqual(self.product1.planned_expiry_date_mode, "exact")
        self.product1.categ_id.planned_expiry_date_mode = "minimal"
        self.assertEqual(self.product1.planned_expiry_date_mode, "minimal")

    def test_compute_planned_expiry_date_mode_overwrite(self):
        self.product1.categ_id.planned_expiry_date_mode = "minimal"
        self.product1.product_tmpl_id.product_planned_expiry_date_mode = "exact"
        self.assertEqual(self.product1.planned_expiry_date_mode, "exact")
        self.product1.categ_id.planned_expiry_date_mode = "exact"
        self.product1.product_tmpl_id.product_planned_expiry_date_mode = "minimal"
        self.assertEqual(self.product1.planned_expiry_date_mode, "minimal")
