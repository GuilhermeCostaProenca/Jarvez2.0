"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Hatchet = void 0;
const Critical_1 = require("../../../../../Attack/Critical");
const DiceRoll_1 = require("../../../../../Dice/DiceRoll");
const EquipmentName_1 = require("../../../EquipmentName");
const WeaponPurpose_1 = require("../../WeaponPurpose");
const MartialWeapon_1 = require("./MartialWeapon");
class Hatchet extends MartialWeapon_1.MartialWeapon {
    constructor() {
        super(...arguments);
        this.damage = Hatchet.damage;
        this.critical = Hatchet.critical;
        this.name = Hatchet.equipmentName;
        this.purposes = Hatchet.purposes;
        this.price = Hatchet.price;
    }
}
exports.Hatchet = Hatchet;
Hatchet.damage = new DiceRoll_1.DiceRoll(1, 6);
Hatchet.critical = new Critical_1.Critical(20, 3);
Hatchet.equipmentName = EquipmentName_1.EquipmentName.hatchet;
Hatchet.purposes = [
    new WeaponPurpose_1.WeaponPurposeMelee(),
    new WeaponPurpose_1.WeaponPurposeRangedThrowing(),
];
Hatchet.price = 6;
