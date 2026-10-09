# Copyright 2026 XtremXpert
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestMoveToProperty(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.group_ids += cls.env.ref("stock.group_stock_multi_locations")
        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.env.company.id)], limit=1
        )
        cls.stock = cls.warehouse.lot_stock_id
        cls.vendor = cls.env["res.partner"].create({"name": "Vendor"})
        cls.owner = cls.env["res.partner"].create({"name": "Owner"})
        cls.product = cls.env["product.product"].create(
            {
                "name": "Fridge",
                "type": "consu",
                "is_storable": True,
                "purchase_ok": True,
            }
        )
        cls.pms_property = cls.env["pms.property"].create(
            {"name": "Putaway Property", "owner_id": cls.owner.id}
        )

    def _receive(self, pms_property=None):
        if pms_property is None:
            pms_property = self.pms_property
        po = self.env["purchase.order"].create(
            {
                "partner_id": self.vendor.id,
                "picking_type_id": self.warehouse.in_type_id.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_qty": 1,
                            "pms_property_id": pms_property.id,
                        },
                    )
                ],
            }
        )
        po.button_confirm()
        return po.picking_ids.move_ids.move_line_ids

    def test_property_location_is_child_of_stock(self):
        location = self.pms_property.stock_location_id
        self.assertEqual(location.warehouse_id, self.warehouse)

    def test_move_to_property(self):
        self.env["stock.putaway.rule"].create(
            {
                "product_id": self.product.id,
                "location_in_id": self.stock.id,
                "move_to_property": True,
            }
        )
        move_lines = self._receive()
        self.assertTrue(move_lines)
        self.assertEqual(
            move_lines.location_dest_id, self.pms_property.stock_location_id
        )

    def test_no_move_to_property(self):
        move_lines = self._receive()
        self.assertTrue(move_lines)
        self.assertNotEqual(
            move_lines.location_dest_id, self.pms_property.stock_location_id
        )

    def test_move_to_property_with_store_to(self):
        shelf = self.env["stock.location"].create(
            {"name": "Shelf", "location_id": self.stock.id, "usage": "internal"}
        )
        self.env["stock.putaway.rule"].create(
            {
                "product_id": self.product.id,
                "location_in_id": self.stock.id,
                "location_out_id": shelf.id,
                "move_to_property": True,
            }
        )
        self.assertEqual(
            self._receive().location_dest_id, self.pms_property.stock_location_id
        )
        # Without a property on the purchase line, the rule stores to "Store to".
        no_property = self.env["pms.property"]
        self.assertEqual(self._receive(no_property).location_dest_id, shelf)
