"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.BastardSword = void 0;
const Critical_1 = require("../../../../../Attack/Critical");
const DiceRoll_1 = require("../../../../../Dice/DiceRoll");
const EquipmentName_1 = require("../../../EquipmentName");
const WeaponPurpose_1 = require("../../WeaponPurpose");
const ExoticWeapon_1 = require("./ExoticWeapon");
class BastardSword extends ExoticWeapon_1.ExoticWeapon {
    constructor() {
        super(...arguments);
        this.damage = BastardSword.damage;
        this.critical = BastardSword.critical;
        this.name = BastardSword.equipmentName;
        this.purposes = BastardSword.purposes;
        this.price = BastardSword.price;
    }
}
exports.BastardSword = BastardSword;
BastardSword.damage = new DiceRoll_1.DiceRoll(1, 10);
BastardSword.critical = new Critical_1.Critical(19, 2);
BastardSword.equipmentName = EquipmentName_1.EquipmentName.bastardSword;
BastardSword.purposes = [
    new WeaponPurpose_1.WeaponPurposeMelee(),
];
BastardSword.price = 35;
