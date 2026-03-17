"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.MountedSpear = void 0;
const Critical_1 = require("../../../../../Attack/Critical");
const DiceRoll_1 = require("../../../../../Dice/DiceRoll");
const EquipmentName_1 = require("../../../EquipmentName");
const WeaponPurpose_1 = require("../../WeaponPurpose");
const MartialWeapon_1 = require("./MartialWeapon");
class MountedSpear extends MartialWeapon_1.MartialWeapon {
    constructor() {
        super(...arguments);
        this.damage = MountedSpear.damage;
        this.critical = MountedSpear.critical;
        this.name = MountedSpear.equipmentName;
        this.purposes = MountedSpear.purposes;
        this.price = MountedSpear.price;
    }
}
exports.MountedSpear = MountedSpear;
MountedSpear.damage = new DiceRoll_1.DiceRoll(1, 8);
MountedSpear.critical = new Critical_1.Critical(20, 3);
MountedSpear.equipmentName = EquipmentName_1.EquipmentName.mountedSpear;
MountedSpear.purposes = [new WeaponPurpose_1.WeaponPurposeMelee()];
MountedSpear.price = 15;
