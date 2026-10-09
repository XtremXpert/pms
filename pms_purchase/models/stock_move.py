# Copyright (c) 2022 Gray Matter Logic
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_pms_property_location(self):
        """Return the property location this move must be put away to.

        The location is returned when a putaway rule of the destination
        location (matching the product, else its category) has
        ``move_to_property`` set, and the property of the purchase order line
        is stocked in the warehouse the purchase order receives into.
        """
        self.ensure_one()
        no_location = self.env["stock.location"]
        line = self.purchase_line_id
        pms_property = line.pms_property_id
        if not pms_property.stock_location_id:
            return no_location
        rules = self.location_dest_id.putaway_rule_ids
        rule = rules.filtered(lambda r: r.product_id == self.product_id)[:1]
        if not rule:
            rule = rules.filtered(
                lambda r: r.category_id == self.product_id.categ_id
            )[:1]
        if not rule.move_to_property:
            return no_location
        po = self.picking_id.purchase_id or line.order_id
        po_warehouse = po.picking_type_id.default_location_dest_id.warehouse_id
        if pms_property.stock_location_id.warehouse_id != po_warehouse:
            return no_location
        return pms_property.stock_location_id
