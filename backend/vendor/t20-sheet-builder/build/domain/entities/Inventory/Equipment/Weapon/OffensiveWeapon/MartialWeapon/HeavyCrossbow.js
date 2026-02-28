"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.HeavyCrossbow = void 0;
const Critical_1 = require("../../../../../Attack/Critical");
const DiceRoll_1 = require("../../../../../Dice/DiceRoll");
const EquipmentName_1 = require("../../../EquipmentName");
const WeaponPurpose_1 = require("../../WeaponPurpose");
const MartialWeapon_1 = require("./MartialWeapon");
class HeavyCrossbow extends MartialWeapon_1.MartialWeapon {
    constructor() {
        super(...arguments);
        this.damage = HeavyCrossbow.damage;
        this.critical = HeavyCrossbow.critical;
        this.name = HeavyCrossbow.equipmentName;
        this.purposes = HeavyCrossbow.purposes;
        this.price = HeavyCrossbow.price;
    }
}
exports.HeavyCrossbow = HeavyCrossbow;
HeavyCrossbow.damage = new DiceRoll_1.DiceRoll(1, 12);
HeavyCrossbow.critical = new Critical_1.Critical(19);
HeavyCrossbow.equipmentName = EquipmentName_1.EquipmentName.heavyCrossbow;
HeavyCrossbow.purposes = [
    new WeaponPurpose_1.WeaponPurposeRangedShooting(),
];
HeavyCrossbow.price = 50;
