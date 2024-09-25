# Copyright 2023-2024 Foodles (https://www.foodles.co/).
# @author Pierre Verkest <pierreverkest84@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import Form, SavepointCase


class AssertReceiptGeneratedFromPurchaseOrder:
    """Unittest mixin to assert Receipt lines generated from
    Purchase order"""

    def assertReceiptLines(self, po, expected_date, expected_pdt_line):
        """Assert quantities in receipt generated from purchase order

        Args:
            po: purchase.order
            expected_date: the expected delivery date (we should get one stock.picking per date)
            expected_pdt_line : a list of tuple with
              * expected_product (product.product)
              * expected_qty (int)
              * expected_planned_expiry_date
        """
        pickings = po.picking_ids.filtered(
            lambda r, planned_date=expected_date: r.scheduled_date.date()
            == fields.Date.from_string(planned_date)
        )
        for (
            expected_product,
            expected_qty,
            expected_planned_expiry_date,
        ) in expected_pdt_line:
            moves = pickings.move_lines.filtered(
                lambda move, pdt=expected_product: move.state not in ("done", "cancel")
                and move.product_id == pdt
            )
            current_qty = sum(moves.mapped("product_uom_qty"))
            self.assertEqual(
                current_qty,
                expected_qty,
                f"Wrong expected received quantities for:\n"
                f" - po: {po.name}\n"
                f" - expected_date: {expected_date}\n"
                f" - product: {expected_product.name}\n"
                f"Current: {current_qty} != Expected: {expected_qty}",
            )
            move_lines = pickings.move_line_ids.filtered(
                lambda move, pdt=expected_product: move.state not in ("done", "cancel")
                and move.product_id == pdt
            )
            for move_line in move_lines:
                self.assertEqual(
                    move_line.planned_expiry_date,
                    fields.Date.from_string(expected_planned_expiry_date)
                    if expected_planned_expiry_date
                    else expected_planned_expiry_date,
                    f"Wrong expected planned_expiry_date for:\n"
                    f" - po: {po.name}\n"
                    f" - expected_date: {expected_date}\n"
                    f" - product: {expected_product.name}\n"
                    f"Current: {move_line.planned_expiry_date} != "
                    f"Expected: {expected_planned_expiry_date}",
                )


@tagged("post_install", "-at_install")
class TestPurchasePlannedExpiryDateCommon(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_id = cls.env["res.partner"].create({"name": "Supplier"})
        cls.product1 = cls.env["product.product"].create(
            {
                "name": "Test Product 1",
                "type": "product",
                "default_code": "PROD1",
                "tracking": "lot",
                "use_expiration_date": True,
                "expiration_time": 1,
                "product_planned_expiry_date_mode": "inherited_from_category",
            }
        )
        cls.product2 = cls.env["product.product"].create(
            {
                "name": "Test Product 2",
                "type": "product",
                "default_code": "PROD2",
                "tracking": "lot",
                "use_expiration_date": True,
                "expiration_time": 1,
                "product_planned_expiry_date_mode": "inherited_from_category",
            }
        )
        cls.product2_bis = cls.env["product.product"].create(
            {
                "product_tmpl_id": cls.product2.product_tmpl_id.id,
                "expiration_time": 1,
                "active": False,
            }
        )
        cls.product3 = cls.env["product.product"].create(
            {
                "name": "Test Product 3 lot tracking without expiry",
                "type": "product",
                "default_code": "PROD3",
                "tracking": "lot",
                "use_expiration_date": False,
            }
        )
        cls.product4 = cls.env["product.product"].create(
            {
                "name": "Test Product no tracking",
                "type": "product",
                "default_code": "PROD4",
                "tracking": "none",
                # I (PV) think it's possible to get such inconsistency
                # values with odoo, in the interface with no tracking
                # use expiration_date is hide but user could set it
                # previously with an other tracking value
                "use_expiration_date": True,
            }
        )

        # dates which we can use to test the features:
        cls.date_planned1 = "2022-06-21"
        cls.date_planned2 = "2022-06-22"
        cls.date_planned3 = "2022-06-23"
        cls.date_planned4 = "2022-06-24"
        cls.date_planned5 = "2022-06-25"

        # Create purchase order
        cls.po = cls.env["purchase.order"].create(
            {
                "partner_id": cls.partner_id.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product1.id,
                            "product_uom": cls.product1.uom_id.id,
                            "name": "[TEST-P1] " + cls.product1.name,
                            "price_unit": cls.product1.standard_price,
                            "date_planned": cls.date_planned1,
                            "planned_expiry_date": cls.date_planned2,
                            "product_qty": 11.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product2.id,
                            "product_uom": cls.product2.uom_id.id,
                            "name": "[TEST-P2] " + cls.product2.name,
                            "price_unit": cls.product2.standard_price,
                            "date_planned": cls.date_planned1,
                            "planned_expiry_date": cls.date_planned3,
                            "product_qty": 22.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product2_bis.id,
                            "product_uom": cls.product2_bis.uom_id.id,
                            "name": "[TEST-P2b] " + cls.product2_bis.name,
                            "price_unit": cls.product2_bis.standard_price,
                            "date_planned": cls.date_planned1,
                            "planned_expiry_date": cls.date_planned3,
                            "product_qty": 122.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product3.id,
                            "product_uom": cls.product3.uom_id.id,
                            "name": "[TEST-P3] " + cls.product3.name,
                            "price_unit": cls.product3.standard_price,
                            "date_planned": cls.date_planned1,
                            "planned_expiry_date": False,
                            "product_qty": 33.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product4.id,
                            "product_uom": cls.product4.uom_id.id,
                            "name": "[TEST-P4] " + cls.product4.name,
                            "price_unit": cls.product4.standard_price,
                            "date_planned": cls.date_planned1,
                            "planned_expiry_date": False,
                            "product_qty": 44.0,
                        },
                    ),
                ],
            }
        )


@tagged("post_install", "-at_install")
class TestPurchasePlannedExpiryDateDraftPo(TestPurchasePlannedExpiryDateCommon):
    def test_purchase_order_line_on_change_product_id(self):
        def is_expected_expiry_date_equal_to_planned(
            po_line, expected_planned_expiry_date
        ):
            return po_line.planned_expiry_date == fields.Date.from_string(
                expected_planned_expiry_date
            )

        self.product1.expiration_time = 3
        with Form(self.po) as po_form:
            for i in range(len(po_form.order_line)):
                with po_form.order_line.edit(i) as pol_form:
                    pol_form.product_id = self.product1
            po_form.save()

        self.assertTrue(
            all(self.po.order_line.mapped(is_expected_expiry_date_equal_to_planned)),
            "Wrong planned_expiry_date for at least one line "
            f"{self.po.order_line.mapped('planned_expiry_date')} "
            f"on change product id expected {self.date_planned4}",
        )


@tagged("post_install", "-at_install")
class TestPurchasePlannedExpiryDateValidatedPo(
    TestPurchasePlannedExpiryDateCommon, AssertReceiptGeneratedFromPurchaseOrder
):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Confirm Purchase Order
        cls.po.button_confirm()

    def test_planned_expiry_date_on_receipt(self):
        self.assertReceiptLines(
            self.po,
            self.date_planned1,
            [
                (self.product1, 11, self.date_planned2),
                (self.product2, 22.0, self.date_planned3),
            ],
        )

    def test_planned_expiry_date_on_receipt_with_different_expiration_time(self):
        self.product2_bis.expiration_time = 3

        with Form(self.po) as po_form:
            for line_index in range(len(po_form.order_line)):
                with po_form.order_line.edit(line_index) as line:
                    line.date_planned = self.date_planned2
            po_form.save()

        self.assertReceiptLines(
            self.po,
            self.date_planned2,
            [
                (self.product2, 22.0, self.date_planned3),
                (self.product2_bis, 122.0, self.date_planned5),
            ],
        )

    def test_receipt_without_planned_expiry_date_on_po(self):
        self.po.order_line.planned_expiry_date = False
        self.assertReceiptLines(
            self.po,
            self.date_planned1,
            [
                (self.product1, 11, False),
                (self.product2, 22.0, False),
            ],
        )

    def test_purchase_order_line_on_change_date_planned(self):
        self.product1.expiration_time = 2
        self.product2.expiration_time = 0

        with Form(self.po) as po_form:
            for line_index in range(len(po_form.order_line)):
                with po_form.order_line.edit(line_index) as line:
                    line.date_planned = self.date_planned2
            po_form.save()

        self.assertReceiptLines(
            self.po,
            self.date_planned2,
            [
                (self.product1, 11, self.date_planned4),
                (self.product2, 22.0, self.date_planned3),
            ],
        )


@tagged("post_install", "-at_install")
class TestPurchasePlannedExpiryDateWarnignsOnValidatedPo(
    TestPurchasePlannedExpiryDateCommon, AssertReceiptGeneratedFromPurchaseOrder
):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Confirm Purchase Order
        cls.po.button_confirm()
        cls.move_line_product1 = cls.po.picking_ids.move_line_ids.filtered(
            lambda move, pdt=cls.product1: move.product_id == pdt
        )
        cls.move_line_product3 = cls.po.picking_ids.move_line_ids.filtered(
            lambda move, pdt=cls.product3: move.product_id == pdt
        )
        cls.move_line_product4 = cls.po.picking_ids.move_line_ids.filtered(
            lambda move, pdt=cls.product4: move.product_id == pdt
        )

    def test_date_expiry_warning_message_no_expiration_date(self):
        self.move_line_product1.expiration_date = False
        self.assertEqual(self.move_line_product1.date_expiry_warning, "")
        self.assertFalse(self.move_line_product4.picking_id.has_expiry_date_warning)

    def test_date_expiry_warning_message_exact_lower(self):
        self.product1.product_tmpl_id.product_planned_expiry_date_mode = "exact"
        self.move_line_product1.expiration_date = self.date_planned1
        self.assertEqual(
            self.move_line_product1.date_expiry_warning,
            "06/22/2022 is the exact expected expiration date.",
        )
        self.assertTrue(self.move_line_product4.picking_id.has_expiry_date_warning)

    def test_date_expiry_warning_message_exact_equal(self):
        self.product1.product_tmpl_id.product_planned_expiry_date_mode = "exact"
        self.move_line_product1.expiration_date = self.date_planned2
        self.assertEqual(self.move_line_product1.date_expiry_warning, "")
        self.assertFalse(self.move_line_product4.picking_id.has_expiry_date_warning)

    def test_date_expiry_warning_message_exact_greater(self):
        self.product1.product_tmpl_id.product_planned_expiry_date_mode = "exact"
        self.move_line_product1.expiration_date = self.date_planned3
        self.assertEqual(
            self.move_line_product1.date_expiry_warning,
            "06/22/2022 is the exact expected expiration date.",
        )
        self.assertTrue(self.move_line_product4.picking_id.has_expiry_date_warning)

    def test_date_expiry_warning_message_minimal_lower(self):
        self.product1.product_tmpl_id.product_planned_expiry_date_mode = "minimal"
        self.move_line_product1.expiration_date = self.date_planned1
        self.assertEqual(
            self.move_line_product1.date_expiry_warning,
            "06/22/2022 is the minimal expiration date expected.",
        )
        self.assertTrue(self.move_line_product4.picking_id.has_expiry_date_warning)

    def test_date_expiry_warning_message_minimal_equal(self):
        self.product1.product_tmpl_id.product_planned_expiry_date_mode = "minimal"
        self.move_line_product1.expiration_date = self.date_planned2
        self.assertEqual(self.move_line_product1.date_expiry_warning, "")
        self.assertFalse(self.move_line_product4.picking_id.has_expiry_date_warning)

    def test_date_expiry_warning_message_minimal_greater(self):
        self.product1.product_tmpl_id.product_planned_expiry_date_mode = "minimal"
        self.move_line_product1.expiration_date = self.date_planned3
        self.assertEqual(self.move_line_product1.date_expiry_warning, "")
        self.assertFalse(self.move_line_product4.picking_id.has_expiry_date_warning)

    def test_date_expiry_warning_message_on_unexpired_tracking_product(self):
        # test weird case where purchase order line expected expiry date would be set
        po_line = self.move_line_product3.move_id.purchase_line_id
        po_line.planned_expiry_date = self.date_planned2
        self.assertEqual(self.move_line_product3.date_expiry_warning, "")
        # kind of ok planned_expiry_date is not displayed
        self.assertEqual(
            self.move_line_product3.planned_expiry_date,
            fields.Date.from_string(self.date_planned2),
        )
        self.assertFalse(self.move_line_product4.picking_id.has_expiry_date_warning)

    def test_date_expiry_warning_message_on_not_tracking_product(self):
        # test weird case where purchase order line expected expiry date would be set
        po_line = self.move_line_product4.move_id.purchase_line_id
        po_line.planned_expiry_date = self.date_planned2
        self.assertEqual(self.move_line_product4.date_expiry_warning, "")
        # kind of ok planned_expiry_date is not displayed
        self.assertEqual(
            self.move_line_product4.planned_expiry_date,
            fields.Date.from_string(self.date_planned2),
        )
        self.assertFalse(self.move_line_product4.picking_id.has_expiry_date_warning)
