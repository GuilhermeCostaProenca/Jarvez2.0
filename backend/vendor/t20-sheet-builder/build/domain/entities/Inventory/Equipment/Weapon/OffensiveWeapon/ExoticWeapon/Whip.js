"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Whip = void 0;
const Critical_1 = require("../../../../../Attack/Critical");
const DiceRoll_1 = require("../../../../../Dice/DiceRoll");
const EquipmentName_1 = require("../../../EquipmentName");
const WeaponPurpose_1 = require("../../WeaponPurpose");
const ExoticWeapon_1 = require("./ExoticWeapon");
class Whip extends ExoticWeapon_1.ExoticWeapon {
    constructor() {
        super(...arguments);
        this.damage = Whip.damage;
        this.critical = Whip.critical;
        this.name = Whip.equipmentName;
        this.purposes = Whip.purposes;
        this.price = Whip.price;
    }
}
exports.Whip = Whip;
Whip.damage = new DiceRoll_1.DiceRoll(1, 3);
Whip.critical = new Critical_1.Critical(20, 2);
Whip.equipmentName = EquipmentName_1.EquipmentName.whip;
Whip.purposes = [
    new WeaponPurpose_1.WeaponPurposeMelee(),
];
Whip.price = 2;
