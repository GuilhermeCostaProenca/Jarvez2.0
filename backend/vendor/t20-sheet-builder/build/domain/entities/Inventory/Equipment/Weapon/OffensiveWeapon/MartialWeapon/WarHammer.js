"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.WarHammer = void 0;
const Critical_1 = require("../../../../../Attack/Critical");
const DiceRoll_1 = require("../../../../../Dice/DiceRoll");
const EquipmentName_1 = require("../../../EquipmentName");
const WeaponPurpose_1 = require("../../WeaponPurpose");
const MartialWeapon_1 = require("./MartialWeapon");
class WarHammer extends MartialWeapon_1.MartialWeapon {
    constructor() {
        super(...arguments);
        this.damage = WarHammer.damage;
        this.critical = WarHammer.critical;
        this.name = WarHammer.equipmentName;
        this.purposes = WarHammer.purposes;
        this.price = WarHammer.price;
    }
}
exports.WarHammer = WarHammer;
WarHammer.damage = new DiceRoll_1.DiceRoll(1, 8);
WarHammer.critical = new Critical_1.Critical(20, 3);
WarHammer.equipmentName = EquipmentName_1.EquipmentName.warHammer;
WarHammer.purposes = [
    new WeaponPurpose_1.WeaponPurposeMelee(),
];
WarHammer.price = 12;
