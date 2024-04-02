/** @odoo-module */

import { useService} from "@web/core/utils/hooks";
import { useSelfOrder } from "@pos_self_order/app/self_order_service";
import { ComboSelection } from "@pos_self_order/app/components/combo_selection/combo_selection";
import { patch } from "@web/core/utils/patch";
import { ProductPopup } from "@odoo_self_order_details/app/components/popup/product_info_popup/product_popup";


patch(ComboSelection.prototype,{
    setup() {
        this.selfOrder = useSelfOrder();
        this.dialog = useService("dialog");

    },

    productClicked(lineId) {
        this.env.currentComboLineId.value = lineId;

        const comboLine = this.props.combo.combo_line_ids.find((line) => line.id == lineId);
        const productSelected = this.selfOrder.productByIds[comboLine.product_id[0]];
        if (!productSelected.self_order_available) {
            return;
        }
        this.props.comboState.selectedProduct = productSelected;
        if (productSelected.attributes.length === 0) {
            this.showProductInformation(productSelected);
            this.props.next();
            return;
        }
        this.props.comboState.showQtyButtons = true;
        this.showProductInformation(productSelected);
    },

    showProductInformation(product) {
        this.dialog.add(ProductPopup, {
            product: product,
            title: product.name,

            addToCart: (qty) => {
            },
        });
    }
});
