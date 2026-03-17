"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ChainofThorns = void 0;
const Critical_1 = require("../../../../../Attack/Critical");
const DiceRoll_1 = require("../../../../../Dice/DiceRoll");
const EquipmentName_1 = require("../../../EquipmentName");
const WeaponPurpose_1 = require("../../WeaponPurpose");
const ExoticWeapon_1 = require("./ExoticWeapon");
class ChainofThorns extends ExoticWeapon_1.ExoticWeapon {
    constructor() {
        super(...arguments);
        this.damage = ChainofThorns.damage;
        this.critical = ChainofThorns.critical;
        this.name = ChainofThorns.equipmentName;
        this.purposes = ChainofThorns.purposes;
        this.price = ChainofThorns.price;
    }
}
exports.ChainofThorns = ChainofThorns;
ChainofThorns.damage = new DiceRoll_1.DiceRoll(2, 4);
ChainofThorns.critical = new Critical_1.Critical(19);
ChainofThorns.equipmentName = EquipmentName_1.EquipmentName.chainofThorns;
ChainofThorns.purposes = [
    new WeaponPurpose_1.WeaponPurposeMelee(),
];
ChainofThorns.price = 25;
