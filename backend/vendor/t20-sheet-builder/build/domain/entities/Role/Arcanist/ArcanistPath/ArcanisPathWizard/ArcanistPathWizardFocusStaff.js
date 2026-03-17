"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArcanistPathWizardFocusStaff = void 0;
const Inventory_1 = require("../../../../Inventory");
const EquipmentWizardFocus_1 = require("../../../../Inventory/Equipment/EquipmentWizardFocus/EquipmentWizardFocus");
const ArcanistPathWizardFocus_1 = require("./ArcanistPathWizardFocus");
class ArcanistPathWizardFocusStaff extends ArcanistPathWizardFocus_1.ArcanistPathWizardFocus {
    constructor() {
        super(new EquipmentWizardFocus_1.EquipmentWizardFocus(Inventory_1.EquipmentName.staff));
    }
}
exports.ArcanistPathWizardFocusStaff = ArcanistPathWizardFocusStaff;
ArcanistPathWizardFocusStaff.equipmentName = Inventory_1.EquipmentName.staff;
