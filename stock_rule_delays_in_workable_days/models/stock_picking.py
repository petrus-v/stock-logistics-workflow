# Copyright (C) 2022 Akretion (<http://www.akretion.com>).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    has_expiry_date_warning = fields.Boolean(
        string="Has expiration date warnings",
        compute="_compute_check_expiration_date_warning",
    )

    @api.depends(
        "move_line_ids.date_expiry_warning",
    )
    def _compute_check_expiration_date_warning(self):
        for rec in self:
            rec.has_expiry_date_warning = any(
                rec.move_line_ids.mapped(lambda line: line.date_expiry_warning != "")
            )
