"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.LongBow = void 0;
const Critical_1 = require("../../../../../Attack/Critical");
const DiceRoll_1 = require("../../../../../Dice/DiceRoll");
const EquipmentName_1 = require("../../../EquipmentName");
const WeaponPurpose_1 = require("../../WeaponPurpose");
const MartialWeapon_1 = require("./MartialWeapon");
class LongBow extends MartialWeapon_1.MartialWeapon {
    constructor() {
        super(...arguments);
        this.damage = LongBow.damage;
        this.critical = LongBow.critical;
        this.name = LongBow.equipmentName;
        this.purposes = LongBow.purposes;
        this.price = LongBow.price;
    }
}
exports.LongBow = LongBow;
LongBow.damage = new DiceRoll_1.DiceRoll(1, 8);
LongBow.critical = new Critical_1.Critical(20, 3);
LongBow.equipmentName = EquipmentName_1.EquipmentName.longBow;
LongBow.purposes = [
    new WeaponPurpose_1.WeaponPurposeRangedShooting(),
];
LongBow.price = 100;
