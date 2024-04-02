/** @odoo-module */


import { ProductCard } from "@pos_self_order/app/components/product_card/product_card";
import { patch } from "@web/core/utils/patch";
import { Line } from "@pos_self_order/app/models/line";
import { constructFullProductName } from "@point_of_sale/utils";
import { ProductPopup } from "@odoo_self_order_details/app/components/popup/product_info_popup/product_popup";

patch(ProductCard.prototype, {
    async selectProduct(qty = 1) {
        const product = this.props.product;

        if (!this.selfOrder.ordering || !product.self_order_available) {
            return;
        }

        if (product.isCombo) {
            this.router.navigate("combo_selection", { id: product.id });
        } else if (product.attributes.length > 0) {
            this.router.navigate("product", { id: product.id });
        } else {
            this.showProductInformation(product);
        }
},

showProductInformation(product) {
    this.dialog.add(ProductPopup, {
        product: this.props.product,
        title: this.props.product.name,
        addToCart: (qty) => {
            const isProductInCart = this.selfOrder.currentOrder.lines.find(
                (line) => line.product_id === product.id
            );

            if (isProductInCart) {
                isProductInCart.qty += qty;
            } else {
                const lines = this.selfOrder.currentOrder.lines;
                const line = new Line({
                    id: null,
                    uuid: null,
                    qty: qty,
                    product_id: product.id,
                });
                line.full_product_name = constructFullProductName(
                    line,
                    this.selfOrder.attributeValueById,
                    product.name
                );
                lines.push(line);
            }
            this.selfOrder.getPricesFromServer();
        },
    });
}
});
