"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ChainMail = void 0;
const EquipmentName_1 = require("../../../../EquipmentName");
const HeavyArmor_1 = require("./HeavyArmor");
class ChainMail extends HeavyArmor_1.HeavyArmor {
    constructor() {
        super(...arguments);
        this.defenseBonus = ChainMail.defenseBonus;
        this.armorPenalty = ChainMail.armorPenalty;
        this.slots = ChainMail.slots;
        this.name = ChainMail.equipmentName;
        this.price = ChainMail.price;
    }
}
exports.ChainMail = ChainMail;
ChainMail.defenseBonus = 6;
ChainMail.armorPenalty = 2;
ChainMail.slots = 5;
ChainMail.equipmentName = EquipmentName_1.EquipmentName.chainMail;
ChainMail.price = 150;
