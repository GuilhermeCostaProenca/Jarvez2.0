"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Assegai = void 0;
const Critical_1 = require("../../../../../Attack/Critical");
const DiceRoll_1 = require("../../../../../Dice/DiceRoll");
const EquipmentName_1 = require("../../../EquipmentName");
const WeaponPurpose_1 = require("../../WeaponPurpose");
const SimpleWeapon_1 = require("./SimpleWeapon");
class Assegai extends SimpleWeapon_1.SimpleWeapon {
    constructor() {
        super(...arguments);
        this.damage = Assegai.damage;
        this.critical = Assegai.critical;
        this.name = Assegai.equipmentName;
        this.purposes = Assegai.purposes;
        this.price = Assegai.price;
    }
}
exports.Assegai = Assegai;
Assegai.damage = new DiceRoll_1.DiceRoll(1, 6);
Assegai.critical = new Critical_1.Critical();
Assegai.equipmentName = EquipmentName_1.EquipmentName.assegai;
Assegai.purposes = [
    new WeaponPurpose_1.WeaponPurposeMelee({
        penalty: 5,
    }),
    new WeaponPurpose_1.WeaponPurposeRangedThrowing(),
];
Assegai.price = 1;
