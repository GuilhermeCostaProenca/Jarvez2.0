"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Accurate = void 0;
const EquipmentImprovement_1 = require("./EquipmentImprovement");
const EquipmentImprovementCategory_1 = require("./EquipmentImprovementCategory");
const EquipmentImprovementName_1 = require("./EquipmentImprovementName");
class Accurate extends EquipmentImprovement_1.EquipmentImprovement {
    constructor() {
        super(...arguments);
        this.name = EquipmentImprovementName_1.EquipmentImprovementName.accurate;
        this.description = '+1 nos testes de ataque';
        this.category = EquipmentImprovementCategory_1.EquipmentImprovementCategory.weapon;
    }
}
exports.Accurate = Accurate;
