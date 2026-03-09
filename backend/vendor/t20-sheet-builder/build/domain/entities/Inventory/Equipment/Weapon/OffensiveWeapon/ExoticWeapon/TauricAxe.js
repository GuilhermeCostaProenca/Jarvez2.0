"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.TauricAxe = void 0;
const Critical_1 = require("../../../../../Attack/Critical");
const DiceRoll_1 = require("../../../../../Dice/DiceRoll");
const EquipmentName_1 = require("../../../EquipmentName");
const WeaponPurpose_1 = require("../../WeaponPurpose");
const ExoticWeapon_1 = require("./ExoticWeapon");
class TauricAxe extends ExoticWeapon_1.ExoticWeapon {
    constructor() {
        super(...arguments);
        this.damage = TauricAxe.damage;
        this.critical = TauricAxe.critical;
        this.name = TauricAxe.equipmentName;
        this.purposes = TauricAxe.purposes;
        this.price = TauricAxe.price;
    }
}
exports.TauricAxe = TauricAxe;
TauricAxe.damage = new DiceRoll_1.DiceRoll(2, 8);
TauricAxe.critical = new Critical_1.Critical(20, 3);
TauricAxe.equipmentName = EquipmentName_1.EquipmentName.tauricAxe;
TauricAxe.purposes = [
    new WeaponPurpose_1.WeaponPurposeMelee(),
];
TauricAxe.price = 50;
