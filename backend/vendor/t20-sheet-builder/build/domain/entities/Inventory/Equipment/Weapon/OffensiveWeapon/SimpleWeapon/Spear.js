"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Spear = void 0;
const Critical_1 = require("../../../../../Attack/Critical");
const DiceRoll_1 = require("../../../../../Dice/DiceRoll");
const EquipmentName_1 = require("../../../EquipmentName");
const WeaponPurpose_1 = require("../../WeaponPurpose");
const SimpleWeapon_1 = require("./SimpleWeapon");
class Spear extends SimpleWeapon_1.SimpleWeapon {
    constructor() {
        super(...arguments);
        this.damage = Spear.damage;
        this.critical = Spear.critical;
        this.name = Spear.equipmentName;
        this.purposes = Spear.purposes;
        this.price = Spear.price;
    }
}
exports.Spear = Spear;
Spear.damage = new DiceRoll_1.DiceRoll(1, 6);
Spear.critical = new Critical_1.Critical();
Spear.equipmentName = EquipmentName_1.EquipmentName.spear;
Spear.purposes = [
    new WeaponPurpose_1.WeaponPurposeMelee(),
    new WeaponPurpose_1.WeaponPurposeRangedThrowing(),
];
Spear.price = 2;
