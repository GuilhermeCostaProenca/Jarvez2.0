"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Club = void 0;
const Critical_1 = require("../../../../../Attack/Critical");
const DiceRoll_1 = require("../../../../../Dice/DiceRoll");
const EquipmentName_1 = require("../../../EquipmentName");
const WeaponPurpose_1 = require("../../WeaponPurpose");
const SimpleWeapon_1 = require("./SimpleWeapon");
class Club extends SimpleWeapon_1.SimpleWeapon {
    constructor() {
        super(...arguments);
        this.damage = Club.damage;
        this.critical = Club.critical;
        this.name = Club.equipmentName;
        this.purposes = Club.purposes;
        this.price = Club.price;
    }
}
exports.Club = Club;
Club.damage = new DiceRoll_1.DiceRoll(1, 6);
Club.critical = new Critical_1.Critical();
Club.equipmentName = EquipmentName_1.EquipmentName.club;
Club.purposes = [
    new WeaponPurpose_1.WeaponPurposeMelee(),
];
Club.price = 0;
