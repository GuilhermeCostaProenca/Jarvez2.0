"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.LightShield = void 0;
const EquipmentName_1 = require("../../../EquipmentName");
const Shield_1 = require("./Shield");
class LightShield extends Shield_1.Shield {
    constructor() {
        super(...arguments);
        this.defenseBonus = 1;
        this.armorPenalty = 1;
        this.slots = 1;
        this.name = EquipmentName_1.EquipmentName.lightShield;
        this.price = 5;
    }
}
exports.LightShield = LightShield;
