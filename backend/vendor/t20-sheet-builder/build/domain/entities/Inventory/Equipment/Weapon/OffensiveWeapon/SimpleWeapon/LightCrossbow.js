"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.LightCrossbow = void 0;
const Critical_1 = require("../../../../../Attack/Critical");
const DiceRoll_1 = require("../../../../../Dice/DiceRoll");
const EquipmentName_1 = require("../../../EquipmentName");
const WeaponPurpose_1 = require("../../WeaponPurpose");
const SimpleWeapon_1 = require("./SimpleWeapon");
class LightCrossbow extends SimpleWeapon_1.SimpleWeapon {
    constructor() {
        super(...arguments);
        this.damage = LightCrossbow.damage;
        this.critical = LightCrossbow.critical;
        this.name = LightCrossbow.equipmentName;
        this.purposes = LightCrossbow.purposes;
        this.price = LightCrossbow.price;
    }
}
exports.LightCrossbow = LightCrossbow;
LightCrossbow.damage = new DiceRoll_1.DiceRoll(1, 8);
LightCrossbow.critical = new Critical_1.Critical(19);
LightCrossbow.equipmentName = EquipmentName_1.EquipmentName.lightCrossbow;
LightCrossbow.purposes = [
    new WeaponPurpose_1.WeaponPurposeRangedShooting(),
];
LightCrossbow.price = 35;
