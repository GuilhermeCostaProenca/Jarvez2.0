"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Trident = void 0;
const Critical_1 = require("../../../../../Attack/Critical");
const DiceRoll_1 = require("../../../../../Dice/DiceRoll");
const EquipmentName_1 = require("../../../EquipmentName");
const WeaponPurpose_1 = require("../../WeaponPurpose");
const MartialWeapon_1 = require("./MartialWeapon");
class Trident extends MartialWeapon_1.MartialWeapon {
    constructor() {
        super(...arguments);
        this.damage = Trident.damage;
        this.critical = Trident.critical;
        this.name = Trident.equipmentName;
        this.purposes = Trident.purposes;
        this.price = Trident.price;
    }
}
exports.Trident = Trident;
Trident.damage = new DiceRoll_1.DiceRoll(1, 8);
Trident.critical = new Critical_1.Critical();
Trident.equipmentName = EquipmentName_1.EquipmentName.trident;
Trident.purposes = [
    new WeaponPurpose_1.WeaponPurposeMelee(),
    new WeaponPurpose_1.WeaponPurposeRangedThrowing(),
];
Trident.price = 15;
