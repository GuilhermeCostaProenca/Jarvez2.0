"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.HandAndaHalfSword = void 0;
const Critical_1 = require("../../../../../Attack/Critical");
const DiceRoll_1 = require("../../../../../Dice/DiceRoll");
const EquipmentName_1 = require("../../../EquipmentName");
const WeaponPurpose_1 = require("../../WeaponPurpose");
const MartialWeapon_1 = require("./MartialWeapon");
class HandAndaHalfSword extends MartialWeapon_1.MartialWeapon {
    constructor() {
        super(...arguments);
        this.damage = HandAndaHalfSword.damage;
        this.critical = HandAndaHalfSword.critical;
        this.name = HandAndaHalfSword.equipmentName;
        this.purposes = HandAndaHalfSword.purposes;
        this.price = HandAndaHalfSword.price;
    }
}
exports.HandAndaHalfSword = HandAndaHalfSword;
HandAndaHalfSword.damage = new DiceRoll_1.DiceRoll(2, 6);
HandAndaHalfSword.critical = new Critical_1.Critical(19);
HandAndaHalfSword.equipmentName = EquipmentName_1.EquipmentName.handAndaHalfSword;
HandAndaHalfSword.purposes = [new WeaponPurpose_1.WeaponPurposeMelee(), new WeaponPurpose_1.WeaponPurposeRangedThrowing()];
HandAndaHalfSword.price = 50;
