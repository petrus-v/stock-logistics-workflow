# Copyright 2023-2024 Foodles (https://www.foodles.co/).
# @author Pierre Verkest <pierreverkest84@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models


class Product(models.Model):
    _inherit = "product.product"

    planned_expiry_date_mode = fields.Selection(
        [("exact", "Exact"), ("minimal", "Minimal")],
        "Result purchase planned expiry date mode",
        compute="_compute_planned_expiry_date_mode",
        help=("Technical field used to get the final values used in code "),
    )

    # even field is not store depends are use-full for cache invalidation
    # at least in unit test
    @api.depends(
        "product_tmpl_id.product_planned_expiry_date_mode",
        "product_tmpl_id.categ_id",
        "product_tmpl_id.categ_id.planned_expiry_date_mode",
    )
    def _compute_planned_expiry_date_mode(self):
        for product in self:
            product.planned_expiry_date_mode = (
                product.product_tmpl_id.product_planned_expiry_date_mode
                if product.product_tmpl_id.product_planned_expiry_date_mode
                != "inherited_from_category"
                else product.categ_id.planned_expiry_date_mode
            )
