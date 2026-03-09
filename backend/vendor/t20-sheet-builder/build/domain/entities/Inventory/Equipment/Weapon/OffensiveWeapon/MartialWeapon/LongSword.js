"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.LongSword = void 0;
const Critical_1 = require("../../../../../Attack/Critical");
const DiceRoll_1 = require("../../../../../Dice/DiceRoll");
const EquipmentName_1 = require("../../../EquipmentName");
const WeaponPurpose_1 = require("../../WeaponPurpose");
const MartialWeapon_1 = require("./MartialWeapon");
class LongSword extends MartialWeapon_1.MartialWeapon {
    constructor() {
        super(...arguments);
        this.damage = LongSword.damage;
        this.critical = LongSword.critical;
        this.name = LongSword.equipmentName;
        this.purposes = LongSword.purposes;
        this.price = LongSword.price;
    }
}
exports.LongSword = LongSword;
LongSword.damage = new DiceRoll_1.DiceRoll(1, 8);
LongSword.critical = new Critical_1.Critical(19);
LongSword.equipmentName = EquipmentName_1.EquipmentName.longSword;
LongSword.purposes = [
    new WeaponPurpose_1.WeaponPurposeMelee(),
];
LongSword.price = 15;
