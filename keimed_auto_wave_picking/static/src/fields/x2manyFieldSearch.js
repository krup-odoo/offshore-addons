/** @odoo-module **/

import { registry } from "@web/core/registry";
import { X2ManyField, x2ManyField } from "@web/views/fields/x2many/x2many_field";


export class x2ManyFieldSearch extends X2ManyField {
    static template = "x2ManyFieldSearchTemplate";
    static components = {
        ...X2ManyField.components,
    }
    // Override
    onInputKeyUp(ev) {
        const value = $(ev.currentTarget).val().toLowerCase();
        $(".o_list_table tr:not(:lt(1))").filter(function() {
            $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
        });
    }
}
registry.category("fields").add("one2manyField_search", {
    ...x2ManyField,
    component: x2ManyFieldSearch,
    additionalClasses: [...x2ManyField.additionalClasses || [], "o_field_one2many"],
});
