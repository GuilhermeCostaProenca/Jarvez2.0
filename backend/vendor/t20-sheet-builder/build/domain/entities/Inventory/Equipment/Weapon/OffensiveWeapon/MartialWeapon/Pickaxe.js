"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Pickaxe = void 0;
const Critical_1 = require("../../../../../Attack/Critical");
const DiceRoll_1 = require("../../../../../Dice/DiceRoll");
const EquipmentName_1 = require("../../../EquipmentName");
const WeaponPurpose_1 = require("../../WeaponPurpose");
const MartialWeapon_1 = require("./MartialWeapon");
class Pickaxe extends MartialWeapon_1.MartialWeapon {
    constructor() {
        super(...arguments);
        this.damage = Pickaxe.damage;
        this.critical = Pickaxe.critical;
        this.name = Pickaxe.equipmentName;
        this.purposes = Pickaxe.purposes;
        this.price = Pickaxe.price;
    }
}
exports.Pickaxe = Pickaxe;
Pickaxe.damage = new DiceRoll_1.DiceRoll(1, 6);
Pickaxe.critical = new Critical_1.Critical(20, 4);
Pickaxe.equipmentName = EquipmentName_1.EquipmentName.pickaxe;
Pickaxe.purposes = [new WeaponPurpose_1.WeaponPurposeMelee()];
Pickaxe.price = 8;
