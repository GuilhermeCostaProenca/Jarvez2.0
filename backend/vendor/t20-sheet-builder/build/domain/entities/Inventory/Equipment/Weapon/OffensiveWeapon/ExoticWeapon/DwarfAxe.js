"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DwarfAxe = void 0;
const Critical_1 = require("../../../../../Attack/Critical");
const DiceRoll_1 = require("../../../../../Dice/DiceRoll");
const EquipmentName_1 = require("../../../EquipmentName");
const WeaponPurpose_1 = require("../../WeaponPurpose");
const ExoticWeapon_1 = require("./ExoticWeapon");
class DwarfAxe extends ExoticWeapon_1.ExoticWeapon {
    constructor() {
        super(...arguments);
        this.damage = DwarfAxe.damage;
        this.critical = DwarfAxe.critical;
        this.name = DwarfAxe.equipmentName;
        this.purposes = DwarfAxe.purposes;
        this.price = DwarfAxe.price;
    }
}
exports.DwarfAxe = DwarfAxe;
DwarfAxe.damage = new DiceRoll_1.DiceRoll(1, 10);
DwarfAxe.critical = new Critical_1.Critical(20, 3);
DwarfAxe.equipmentName = EquipmentName_1.EquipmentName.dwarfAxe;
DwarfAxe.purposes = [
    new WeaponPurpose_1.WeaponPurposeMelee(),
];
DwarfAxe.price = 30;
