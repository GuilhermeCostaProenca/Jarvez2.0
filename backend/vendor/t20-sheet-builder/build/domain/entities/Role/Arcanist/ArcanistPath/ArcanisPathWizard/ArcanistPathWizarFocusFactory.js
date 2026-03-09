"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArcanistPathWizardFocusFactory = void 0;
const errors_1 = require("../../../../../errors");
const Inventory_1 = require("../../../../Inventory");
const ArcanistPathWizardFocusStaff_1 = require("./ArcanistPathWizardFocusStaff");
const ArcanistPathWizardFocusWand_1 = require("./ArcanistPathWizardFocusWand");
class ArcanistPathWizardFocusFactory {
    static make(focus) {
        if (focus === Inventory_1.EquipmentName.staff) {
            return new ArcanistPathWizardFocusStaff_1.ArcanistPathWizardFocusStaff();
        }
        if (focus === Inventory_1.EquipmentName.wand) {
            return new ArcanistPathWizardFocusWand_1.ArcanistPathWizardFocusWand();
        }
        throw new errors_1.SheetBuilderError('INVALID_WIZARD_FOCUS');
    }
}
exports.ArcanistPathWizardFocusFactory = ArcanistPathWizardFocusFactory;
