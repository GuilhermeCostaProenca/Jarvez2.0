"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Baton = void 0;
const Critical_1 = require("../../../../../Attack/Critical");
const DiceRoll_1 = require("../../../../../Dice/DiceRoll");
const EquipmentName_1 = require("../../../EquipmentName");
const WeaponPurpose_1 = require("../../WeaponPurpose");
const SimpleWeapon_1 = require("./SimpleWeapon");
class Baton extends SimpleWeapon_1.SimpleWeapon {
    constructor() {
        super(...arguments);
        this.damage = Baton.damage;
        this.critical = Baton.critical;
        this.name = Baton.equipmentName;
        this.purposes = Baton.purposes;
        this.price = Baton.price;
    }
}
exports.Baton = Baton;
Baton.damage = new DiceRoll_1.DiceRoll(1, 10);
Baton.critical = new Critical_1.Critical();
Baton.equipmentName = EquipmentName_1.EquipmentName.baton;
Baton.purposes = [
    new WeaponPurpose_1.WeaponPurposeMelee(),
];
Baton.price = 0;
