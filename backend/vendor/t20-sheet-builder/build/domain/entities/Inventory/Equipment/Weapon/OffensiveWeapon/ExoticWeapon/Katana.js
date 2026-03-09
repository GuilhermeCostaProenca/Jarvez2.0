"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Katana = void 0;
const Critical_1 = require("../../../../../Attack/Critical");
const DiceRoll_1 = require("../../../../../Dice/DiceRoll");
const EquipmentName_1 = require("../../../EquipmentName");
const WeaponPurpose_1 = require("../../WeaponPurpose");
const ExoticWeapon_1 = require("./ExoticWeapon");
class Katana extends ExoticWeapon_1.ExoticWeapon {
    constructor() {
        super(...arguments);
        this.damage = Katana.damage;
        this.critical = Katana.critical;
        this.name = Katana.equipmentName;
        this.purposes = Katana.purposes;
        this.price = Katana.price;
    }
}
exports.Katana = Katana;
Katana.damage = new DiceRoll_1.DiceRoll(1, 10);
Katana.critical = new Critical_1.Critical(19, 2);
Katana.equipmentName = EquipmentName_1.EquipmentName.katana;
Katana.purposes = [
    new WeaponPurpose_1.WeaponPurposeMelee(),
];
Katana.price = 100;
