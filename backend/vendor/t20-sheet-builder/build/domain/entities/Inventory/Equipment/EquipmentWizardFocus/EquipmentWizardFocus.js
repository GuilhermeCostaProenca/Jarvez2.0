"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.EquipmentWizardFocus = void 0;
const Equipment_1 = require("../Equipment");
class EquipmentWizardFocus extends Equipment_1.Equipment {
    constructor(name, isWieldable = false, price = 0) {
        super();
        this.name = name;
        this.isWieldable = isWieldable;
        this.price = price;
        this.categoryForImprovement = null;
    }
}
exports.EquipmentWizardFocus = EquipmentWizardFocus;
