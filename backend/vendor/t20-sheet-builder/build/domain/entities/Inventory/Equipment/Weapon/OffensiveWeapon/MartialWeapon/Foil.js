"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Foil = void 0;
const Critical_1 = require("../../../../../Attack/Critical");
const DiceRoll_1 = require("../../../../../Dice/DiceRoll");
const EquipmentName_1 = require("../../../EquipmentName");
const WeaponPurpose_1 = require("../../WeaponPurpose");
const MartialWeapon_1 = require("./MartialWeapon");
class Foil extends MartialWeapon_1.MartialWeapon {
    constructor() {
        super(...arguments);
        this.damage = Foil.damage;
        this.critical = Foil.critical;
        this.name = Foil.equipmentName;
        this.purposes = Foil.purposes;
        this.price = Foil.price;
    }
}
exports.Foil = Foil;
Foil.damage = new DiceRoll_1.DiceRoll(1, 6);
Foil.critical = new Critical_1.Critical(18);
Foil.equipmentName = EquipmentName_1.EquipmentName.foil;
Foil.purposes = [new WeaponPurpose_1.WeaponPurposeMelee()];
Foil.price = 20;
