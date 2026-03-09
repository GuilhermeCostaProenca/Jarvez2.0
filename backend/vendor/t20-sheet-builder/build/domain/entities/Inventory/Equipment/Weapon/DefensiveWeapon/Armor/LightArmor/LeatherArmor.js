"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.LeatherArmor = void 0;
const EquipmentName_1 = require("../../../../EquipmentName");
const LightArmor_1 = require("./LightArmor");
class LeatherArmor extends LightArmor_1.LightArmor {
    constructor() {
        super(...arguments);
        this.defenseBonus = LeatherArmor.defenseBonus;
        this.armorPenalty = LeatherArmor.armorPenalty;
        this.slots = LeatherArmor.slots;
        this.name = LeatherArmor.equipmentName;
        this.price = LeatherArmor.price;
    }
}
exports.LeatherArmor = LeatherArmor;
LeatherArmor.defenseBonus = 2;
LeatherArmor.armorPenalty = 0;
LeatherArmor.slots = 2;
LeatherArmor.equipmentName = EquipmentName_1.EquipmentName.leatherArmor;
LeatherArmor.price = 20;
