"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.HeavyShield = void 0;
const EquipmentName_1 = require("../../../EquipmentName");
const Shield_1 = require("./Shield");
class HeavyShield extends Shield_1.Shield {
    constructor() {
        super(...arguments);
        this.defenseBonus = 2;
        this.armorPenalty = 2;
        this.slots = 2;
        this.name = EquipmentName_1.EquipmentName.heavyShield;
        this.price = 15;
    }
}
exports.HeavyShield = HeavyShield;
