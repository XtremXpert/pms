# Copyright (c) 2022 Gray Matter Logic
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class PmsProperty(models.Model):
    _inherit = "pms.property"

    stock_location_id = fields.Many2one("stock.location", string="Inventory Location")

    @api.model_create_multi
    def create(self, vals_list):
        recs = super().create(vals_list)
        for rec in recs:
            if not rec.stock_location_id:
                rec._create_stock_location()
        return recs

    def write(self, vals):
        res = super().write(vals)
        if "name" in vals:
            for rec in self:
                if rec.stock_location_id:
                    rec.stock_location_id.name = rec.name
                else:
                    rec._create_stock_location()
        return res

    def _create_stock_location(self):
        parent = self.env.ref("stock.stock_location_stock", raise_if_not_found=False)
        if not parent:
            return
        # The user may not see the stock location of another company.
        parent = parent.sudo()
        # Odoo 20 rejects a location whose company differs from its parent's:
        # for a property of another company, use that company's warehouse.
        company = self.company_id or self.env.company
        if parent.company_id and parent.company_id != company:
            warehouse = (
                self.env["stock.warehouse"]
                .sudo()
                .search([("company_id", "=", company.id)], limit=1)
            )
            parent = warehouse.lot_stock_id or parent
        location = (
            self.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": self.name,
                    "location_id": parent.id,
                    "usage": "internal",
                    "company_id": parent.company_id.id,
                }
            )
        )
        self.stock_location_id = location.id
