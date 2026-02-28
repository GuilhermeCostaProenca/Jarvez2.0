"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.FullPlate = void 0;
const EquipmentName_1 = require("../../../../EquipmentName");
const HeavyArmor_1 = require("./HeavyArmor");
class FullPlate extends HeavyArmor_1.HeavyArmor {
    constructor() {
        super(...arguments);
        this.defenseBonus = FullPlate.defenseBonus;
        this.armorPenalty = FullPlate.armorPenalty;
        this.slots = FullPlate.slots;
        this.name = FullPlate.equipmentName;
        this.price = FullPlate.price;
    }
}
exports.FullPlate = FullPlate;
FullPlate.defenseBonus = 10;
FullPlate.armorPenalty = 5;
FullPlate.slots = 5;
FullPlate.equipmentName = EquipmentName_1.EquipmentName.fullPlate;
FullPlate.price = 3000;
