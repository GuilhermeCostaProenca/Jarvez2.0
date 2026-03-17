"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Cruel = void 0;
const EquipmentImprovement_1 = require("./EquipmentImprovement");
const EquipmentImprovementCategory_1 = require("./EquipmentImprovementCategory");
const EquipmentImprovementName_1 = require("./EquipmentImprovementName");
class Cruel extends EquipmentImprovement_1.EquipmentImprovement {
    constructor() {
        super(...arguments);
        this.name = EquipmentImprovementName_1.EquipmentImprovementName.cruel;
        this.description = '+1 nas rolagens de dano';
        this.category = EquipmentImprovementCategory_1.EquipmentImprovementCategory.weapon;
    }
}
exports.Cruel = Cruel;
