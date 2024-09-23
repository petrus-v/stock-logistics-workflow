# Copyright 2023-2024 Foodles (https://www.foodles.co/).
# @author Pierre Verkest <pierreverkest84@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = "product.category"

    planned_expiry_date_mode = fields.Selection(
        [("exact", "Exact"), ("minimal", "Minimal")],
        "Purchase planned expiry date mode",
        required=True,
        default="exact",
        help=(
            "Kind of planned expiry date collected on purchase order line to manage "
            "warning according:\n"
            "the expiry date set on lot while receiving products:\n"
            " * Exact: If the dates doesn't matched a warning is shown.\n"
            " * Minimal: warning will be shown if expiry date is before the 'minimal' "
            "planned expiry date.\n"
        ),
    )
