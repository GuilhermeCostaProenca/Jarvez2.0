"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.StaffStick = void 0;
const Critical_1 = require("../../../../../Attack/Critical");
const DiceRoll_1 = require("../../../../../Dice/DiceRoll");
const EquipmentName_1 = require("../../../EquipmentName");
const WeaponPurpose_1 = require("../../WeaponPurpose");
const SimpleWeapon_1 = require("./SimpleWeapon");
class StaffStick extends SimpleWeapon_1.SimpleWeapon {
    constructor() {
        super(...arguments);
        this.damage = StaffStick.damage;
        this.critical = StaffStick.critical;
        this.name = StaffStick.equipmentName;
        this.purposes = StaffStick.purposes;
        this.price = StaffStick.price;
    }
}
exports.StaffStick = StaffStick;
StaffStick.damage = new DiceRoll_1.DiceRoll(1, 6);
StaffStick.critical = new Critical_1.Critical();
StaffStick.equipmentName = EquipmentName_1.EquipmentName.staffStick;
StaffStick.purposes = [
    new WeaponPurpose_1.WeaponPurposeMelee(),
];
StaffStick.price = 0;
