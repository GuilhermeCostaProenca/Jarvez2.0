"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Scythe = void 0;
const Critical_1 = require("../../../../../Attack/Critical");
const DiceRoll_1 = require("../../../../../Dice/DiceRoll");
const EquipmentName_1 = require("../../../EquipmentName");
const WeaponPurpose_1 = require("../../WeaponPurpose");
const MartialWeapon_1 = require("./MartialWeapon");
class Scythe extends MartialWeapon_1.MartialWeapon {
    constructor() {
        super(...arguments);
        this.damage = Scythe.damage;
        this.critical = Scythe.critical;
        this.name = Scythe.equipmentName;
        this.purposes = Scythe.purposes;
        this.price = Scythe.price;
    }
}
exports.Scythe = Scythe;
Scythe.damage = new DiceRoll_1.DiceRoll(2, 4);
Scythe.critical = new Critical_1.Critical(20, 4);
Scythe.equipmentName = EquipmentName_1.EquipmentName.scythe;
Scythe.purposes = [new WeaponPurpose_1.WeaponPurposeMelee()];
Scythe.price = 18;
