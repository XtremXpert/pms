# Copyright 2026 XtremXpert
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def _apply_putaway_strategy(self):
        res = super()._apply_putaway_strategy()
        if self.env.context.get("avoid_putaway_rules"):
            return res
        for sml in self:
            location = sml.move_id and sml.move_id._get_pms_property_location()
            if location and sml.location_dest_id != location:
                sml.location_dest_id = location
        return res
