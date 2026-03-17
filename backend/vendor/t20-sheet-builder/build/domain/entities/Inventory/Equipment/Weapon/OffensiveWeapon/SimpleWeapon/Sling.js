"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Sling = void 0;
const Critical_1 = require("../../../../../Attack/Critical");
const DiceRoll_1 = require("../../../../../Dice/DiceRoll");
const EquipmentName_1 = require("../../../EquipmentName");
const WeaponPurpose_1 = require("../../WeaponPurpose");
const SimpleWeapon_1 = require("./SimpleWeapon");
class Sling extends SimpleWeapon_1.SimpleWeapon {
    constructor() {
        super(...arguments);
        this.damage = Sling.damage;
        this.critical = Sling.critical;
        this.name = Sling.equipmentName;
        this.purposes = Sling.purposes;
        this.price = Sling.price;
    }
}
exports.Sling = Sling;
Sling.damage = new DiceRoll_1.DiceRoll(1, 4);
Sling.critical = new Critical_1.Critical();
Sling.equipmentName = EquipmentName_1.EquipmentName.sling;
Sling.purposes = [
    new WeaponPurpose_1.WeaponPurposeRangedShooting({
        damageAttribute: 'strength',
    }),
];
Sling.price = 0;
