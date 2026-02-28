"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Mace = void 0;
const Critical_1 = require("../../../../../Attack/Critical");
const DiceRoll_1 = require("../../../../../Dice/DiceRoll");
const EquipmentName_1 = require("../../../EquipmentName");
const WeaponPurpose_1 = require("../../WeaponPurpose");
const SimpleWeapon_1 = require("./SimpleWeapon");
class Mace extends SimpleWeapon_1.SimpleWeapon {
    constructor() {
        super(...arguments);
        this.damage = Mace.damage;
        this.critical = Mace.critical;
        this.name = Mace.equipmentName;
        this.purposes = Mace.purposes;
        this.price = Mace.price;
    }
}
exports.Mace = Mace;
Mace.damage = new DiceRoll_1.DiceRoll(1, 8);
Mace.critical = new Critical_1.Critical();
Mace.equipmentName = EquipmentName_1.EquipmentName.mace;
Mace.purposes = [
    new WeaponPurpose_1.WeaponPurposeMelee(),
];
Mace.price = 12;
