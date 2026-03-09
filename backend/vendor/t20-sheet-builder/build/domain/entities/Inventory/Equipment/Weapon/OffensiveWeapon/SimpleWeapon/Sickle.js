"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Sickle = void 0;
const Critical_1 = require("../../../../../Attack/Critical");
const DiceRoll_1 = require("../../../../../Dice/DiceRoll");
const EquipmentName_1 = require("../../../EquipmentName");
const WeaponPurpose_1 = require("../../WeaponPurpose");
const SimpleWeapon_1 = require("./SimpleWeapon");
class Sickle extends SimpleWeapon_1.SimpleWeapon {
    constructor() {
        super(...arguments);
        this.damage = Sickle.damage;
        this.critical = Sickle.critical;
        this.name = Sickle.equipmentName;
        this.purposes = Sickle.purposes;
        this.price = Sickle.price;
    }
}
exports.Sickle = Sickle;
Sickle.damage = new DiceRoll_1.DiceRoll(1, 6);
Sickle.critical = new Critical_1.Critical(20, 3);
Sickle.equipmentName = EquipmentName_1.EquipmentName.sickle;
Sickle.purposes = [
    new WeaponPurpose_1.WeaponPurposeMelee(),
];
Sickle.price = 4;
