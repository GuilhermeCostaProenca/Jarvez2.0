"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ShortSword = void 0;
const Critical_1 = require("../../../../../Attack/Critical");
const DiceRoll_1 = require("../../../../../Dice/DiceRoll");
const EquipmentName_1 = require("../../../EquipmentName");
const WeaponPurpose_1 = require("../../WeaponPurpose");
const SimpleWeapon_1 = require("./SimpleWeapon");
class ShortSword extends SimpleWeapon_1.SimpleWeapon {
    constructor() {
        super(...arguments);
        this.damage = ShortSword.damage;
        this.critical = ShortSword.critical;
        this.name = ShortSword.equipmentName;
        this.purposes = ShortSword.purposes;
        this.price = ShortSword.price;
    }
}
exports.ShortSword = ShortSword;
ShortSword.damage = new DiceRoll_1.DiceRoll(1, 6);
ShortSword.critical = new Critical_1.Critical(19);
ShortSword.equipmentName = EquipmentName_1.EquipmentName.shortSword;
ShortSword.purposes = [
    new WeaponPurpose_1.WeaponPurposeMelee(),
];
ShortSword.price = 10;
