"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.StuddedLeatherArmor = void 0;
const EquipmentName_1 = require("../../../../EquipmentName");
const LightArmor_1 = require("./LightArmor");
class StuddedLeatherArmor extends LightArmor_1.LightArmor {
    constructor() {
        super(...arguments);
        this.defenseBonus = StuddedLeatherArmor.defenseBonus;
        this.armorPenalty = StuddedLeatherArmor.armorPenalty;
        this.slots = StuddedLeatherArmor.slots;
        this.name = StuddedLeatherArmor.equipmentName;
        this.price = StuddedLeatherArmor.price;
    }
}
exports.StuddedLeatherArmor = StuddedLeatherArmor;
StuddedLeatherArmor.defenseBonus = 3;
StuddedLeatherArmor.armorPenalty = 1;
StuddedLeatherArmor.slots = 2;
StuddedLeatherArmor.equipmentName = EquipmentName_1.EquipmentName.studdedLeather;
StuddedLeatherArmor.price = 35;
