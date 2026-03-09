"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Horns = void 0;
const Critical_1 = require("../../../../../Attack/Critical");
const DiceRoll_1 = require("../../../../../Dice/DiceRoll");
const EquipmentName_1 = require("../../../EquipmentName");
const WeaponPurpose_1 = require("../../WeaponPurpose");
const SimpleWeapon_1 = require("./SimpleWeapon");
class Horns extends SimpleWeapon_1.SimpleWeapon {
    constructor() {
        super(...arguments);
        this.damage = Horns.damage;
        this.critical = Horns.critical;
        this.name = Horns.equipmentName;
        this.purposes = Horns.purposes;
        this.price = Horns.price;
    }
}
exports.Horns = Horns;
Horns.damage = new DiceRoll_1.DiceRoll(1, 6);
Horns.critical = new Critical_1.Critical();
Horns.equipmentName = EquipmentName_1.EquipmentName.horns;
Horns.purposes = [
    new WeaponPurpose_1.WeaponPurposeMelee(),
];
Horns.price = 0;
