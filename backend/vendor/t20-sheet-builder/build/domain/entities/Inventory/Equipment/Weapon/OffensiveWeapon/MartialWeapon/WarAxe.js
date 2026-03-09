"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.WarAxe = void 0;
const Critical_1 = require("../../../../../Attack/Critical");
const DiceRoll_1 = require("../../../../../Dice/DiceRoll");
const EquipmentName_1 = require("../../../EquipmentName");
const WeaponPurpose_1 = require("../../WeaponPurpose");
const MartialWeapon_1 = require("./MartialWeapon");
class WarAxe extends MartialWeapon_1.MartialWeapon {
    constructor() {
        super(...arguments);
        this.damage = WarAxe.damage;
        this.critical = WarAxe.critical;
        this.name = WarAxe.equipmentName;
        this.purposes = WarAxe.purposes;
        this.price = WarAxe.price;
    }
}
exports.WarAxe = WarAxe;
WarAxe.damage = new DiceRoll_1.DiceRoll(1, 12);
WarAxe.critical = new Critical_1.Critical(20, 3);
WarAxe.equipmentName = EquipmentName_1.EquipmentName.warAxe;
WarAxe.purposes = [
    new WeaponPurpose_1.WeaponPurposeMelee(),
];
WarAxe.price = 20;
