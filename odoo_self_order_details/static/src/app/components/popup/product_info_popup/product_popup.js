/** @odoo-module */

import {  Component,useExternalListener, useState } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";

export class ProductPopup extends Component {
    static template = "odoo_self_order_details.ProductPopup";
    static props = ["product", "addToCart"];

    setup() {
        useExternalListener(window, "click", this.props.close);
        this.state = useState({
            qty: 1,
        });
    }
    addToCartAndClose() {
        this.props.addToCart(this.state.qty);
        this.props.close();
    }

}
