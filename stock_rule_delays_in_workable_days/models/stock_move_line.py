# Copyright 2023-2024 Foodles (https://www.foodles.co/).
# @author Pierre Verkest <pierreverkest84@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import _, api, fields, models
from odoo.tools import format_date


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    planned_expiry_date = fields.Date(
        compute="_compute_planned_expiry_date_and_warnings",
    )
    date_expiry_warning = fields.Char(
        string="Expiration date warning",
        compute="_compute_planned_expiry_date_and_warnings",
    )

    @api.depends(
        "expiration_date",
        "move_id.purchase_line_id.planned_expiry_date",
        "product_id.tracking",
        "product_id.use_expiration_date",
    )
    def _compute_planned_expiry_date_and_warnings(self):
        for stock_move_line in self:
            stock_move_line.date_expiry_warning = ""
            stock_move_line.planned_expiry_date = (
                stock_move_line.move_id.purchase_line_id.planned_expiry_date or False
            )
            if (
                stock_move_line.expiration_date
                and stock_move_line.planned_expiry_date
                and stock_move_line.product_id.tracking
                and stock_move_line.product_id.use_expiration_date
            ):
                if (
                    stock_move_line.product_id.planned_expiry_date_mode == "exact"
                    and stock_move_line.expiration_date.date()
                    != stock_move_line.planned_expiry_date
                ):
                    stock_move_line.date_expiry_warning = _(
                        "%(expected_date)s is the exact expected expiration date."
                    ) % dict(
                        expected_date=format_date(
                            self.env, stock_move_line.planned_expiry_date
                        )
                    )
                if (
                    stock_move_line.product_id.planned_expiry_date_mode == "minimal"
                    and stock_move_line.expiration_date.date()
                    < stock_move_line.planned_expiry_date
                ):
                    stock_move_line.date_expiry_warning = _(
                        "%(expected_date)s is the minimal expiration date expected."
                    ) % dict(
                        expected_date=format_date(
                            self.env, stock_move_line.planned_expiry_date
                        )
                    )
