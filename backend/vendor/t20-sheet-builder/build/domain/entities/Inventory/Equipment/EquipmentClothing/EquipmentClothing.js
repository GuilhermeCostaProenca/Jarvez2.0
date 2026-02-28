"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.EquipmentClothing = void 0;
const Equipment_1 = require("../Equipment");
const EquipmentImprovementCategory_1 = require("../EquipmentImprovement/EquipmentImprovementCategory");
class EquipmentClothing extends Equipment_1.Equipment {
    get isWieldable() {
        return false;
    }
    constructor(name, price = 0) {
        super();
        this.name = name;
        this.price = price;
        this.categoryForImprovement = EquipmentImprovementCategory_1.EquipmentImprovementCategory.toolsAndClothing;
    }
}
exports.EquipmentClothing = EquipmentClothing;
