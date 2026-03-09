"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Flail = void 0;
const Critical_1 = require("../../../../../Attack/Critical");
const DiceRoll_1 = require("../../../../../Dice/DiceRoll");
const EquipmentName_1 = require("../../../EquipmentName");
const WeaponPurpose_1 = require("../../WeaponPurpose");
const MartialWeapon_1 = require("./MartialWeapon");
class Flail extends MartialWeapon_1.MartialWeapon {
    constructor() {
        super(...arguments);
        this.damage = Flail.damage;
        this.critical = Flail.critical;
        this.name = Flail.equipmentName;
        this.purposes = Flail.purposes;
        this.price = Flail.price;
    }
}
exports.Flail = Flail;
Flail.damage = new DiceRoll_1.DiceRoll(1, 8);
Flail.critical = new Critical_1.Critical();
Flail.equipmentName = EquipmentName_1.EquipmentName.flail;
Flail.purposes = [new WeaponPurpose_1.WeaponPurposeMelee()];
Flail.price = 8;
