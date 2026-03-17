"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Fit = void 0;
const EquipmentImprovement_1 = require("./EquipmentImprovement");
const EquipmentImprovementCategory_1 = require("./EquipmentImprovementCategory");
const EquipmentImprovementName_1 = require("./EquipmentImprovementName");
class Fit extends EquipmentImprovement_1.EquipmentImprovement {
    constructor() {
        super(...arguments);
        this.name = EquipmentImprovementName_1.EquipmentImprovementName.fit;
        this.description = '-1 na penalidade de armadura';
        this.category = EquipmentImprovementCategory_1.EquipmentImprovementCategory.armorAndShield;
    }
}
exports.Fit = Fit;
