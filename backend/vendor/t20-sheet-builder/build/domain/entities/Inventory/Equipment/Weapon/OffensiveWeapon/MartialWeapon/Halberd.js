"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Halberd = void 0;
const Critical_1 = require("../../../../../Attack/Critical");
const DiceRoll_1 = require("../../../../../Dice/DiceRoll");
const EquipmentName_1 = require("../../../EquipmentName");
const WeaponPurpose_1 = require("../../WeaponPurpose");
const MartialWeapon_1 = require("./MartialWeapon");
class Halberd extends MartialWeapon_1.MartialWeapon {
    constructor() {
        super(...arguments);
        this.damage = Halberd.damage;
        this.critical = Halberd.critical;
        this.name = Halberd.equipmentName;
        this.purposes = Halberd.purposes;
        this.price = Halberd.price;
    }
}
exports.Halberd = Halberd;
Halberd.damage = new DiceRoll_1.DiceRoll(1, 10);
Halberd.critical = new Critical_1.Critical(20, 3);
Halberd.equipmentName = EquipmentName_1.EquipmentName.halberd;
Halberd.purposes = [new WeaponPurpose_1.WeaponPurposeMelee()];
Halberd.price = 10;
