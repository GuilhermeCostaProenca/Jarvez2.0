"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Pike = void 0;
const Critical_1 = require("../../../../../Attack/Critical");
const DiceRoll_1 = require("../../../../../Dice/DiceRoll");
const EquipmentName_1 = require("../../../EquipmentName");
const WeaponPurpose_1 = require("../../WeaponPurpose");
const SimpleWeapon_1 = require("./SimpleWeapon");
class Pike extends SimpleWeapon_1.SimpleWeapon {
    constructor() {
        super(...arguments);
        this.damage = Pike.damage;
        this.critical = Pike.critical;
        this.name = Pike.equipmentName;
        this.purposes = Pike.purposes;
        this.price = Pike.price;
    }
}
exports.Pike = Pike;
Pike.damage = new DiceRoll_1.DiceRoll(1, 8);
Pike.critical = new Critical_1.Critical();
Pike.equipmentName = EquipmentName_1.EquipmentName.pike;
Pike.purposes = [
    new WeaponPurpose_1.WeaponPurposeMelee(),
];
Pike.price = 2;
