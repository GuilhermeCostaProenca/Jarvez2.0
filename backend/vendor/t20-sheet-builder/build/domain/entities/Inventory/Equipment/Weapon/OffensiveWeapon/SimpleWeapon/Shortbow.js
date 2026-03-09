"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Shortbow = void 0;
const Critical_1 = require("../../../../../Attack/Critical");
const DiceRoll_1 = require("../../../../../Dice/DiceRoll");
const EquipmentName_1 = require("../../../EquipmentName");
const WeaponPurpose_1 = require("../../WeaponPurpose");
const SimpleWeapon_1 = require("./SimpleWeapon");
class Shortbow extends SimpleWeapon_1.SimpleWeapon {
    constructor() {
        super(...arguments);
        this.damage = Shortbow.damage;
        this.critical = Shortbow.critical;
        this.name = Shortbow.equipmentName;
        this.purposes = Shortbow.purposes;
        this.price = Shortbow.price;
    }
}
exports.Shortbow = Shortbow;
Shortbow.damage = new DiceRoll_1.DiceRoll(1, 4);
Shortbow.critical = new Critical_1.Critical(20, 3);
Shortbow.equipmentName = EquipmentName_1.EquipmentName.shortbow;
Shortbow.purposes = [
    new WeaponPurpose_1.WeaponPurposeRangedShooting(),
];
Shortbow.price = 30;
