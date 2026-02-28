"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.EquipmentAlchemic = void 0;
const Equipment_1 = require("../Equipment");
class EquipmentAlchemic extends Equipment_1.Equipment {
    constructor() {
        super(...arguments);
        this.categoryForImprovement = null;
    }
}
exports.EquipmentAlchemic = EquipmentAlchemic;
