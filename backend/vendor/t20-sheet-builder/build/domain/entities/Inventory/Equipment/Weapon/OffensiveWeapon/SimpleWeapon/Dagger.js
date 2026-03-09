"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Dagger = void 0;
const Critical_1 = require("../../../../../Attack/Critical");
const DiceRoll_1 = require("../../../../../Dice/DiceRoll");
const EquipmentName_1 = require("../../../EquipmentName");
const WeaponPurpose_1 = require("../../WeaponPurpose");
const SimpleWeapon_1 = require("./SimpleWeapon");
class Dagger extends SimpleWeapon_1.SimpleWeapon {
    constructor() {
        super(...arguments);
        this.damage = Dagger.damage;
        this.critical = Dagger.critical;
        this.name = Dagger.equipmentName;
        this.purposes = Dagger.purposes;
        this.price = Dagger.price;
    }
}
exports.Dagger = Dagger;
Dagger.damage = new DiceRoll_1.DiceRoll(1, 4);
Dagger.critical = new Critical_1.Critical(19);
Dagger.equipmentName = EquipmentName_1.EquipmentName.dagger;
Dagger.purposes = [
    new WeaponPurpose_1.WeaponPurposeMelee({
        customTestAttributes: new Set(['dexterity']),
    }),
    new WeaponPurpose_1.WeaponPurposeRangedThrowing(),
];
Dagger.price = 2;
