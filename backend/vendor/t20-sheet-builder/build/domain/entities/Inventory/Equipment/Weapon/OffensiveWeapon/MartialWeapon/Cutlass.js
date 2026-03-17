"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Cutlass = void 0;
const Critical_1 = require("../../../../../Attack/Critical");
const DiceRoll_1 = require("../../../../../Dice/DiceRoll");
const EquipmentName_1 = require("../../../EquipmentName");
const WeaponPurpose_1 = require("../../WeaponPurpose");
const MartialWeapon_1 = require("./MartialWeapon");
class Cutlass extends MartialWeapon_1.MartialWeapon {
    constructor() {
        super(...arguments);
        this.damage = Cutlass.damage;
        this.critical = Cutlass.critical;
        this.name = Cutlass.equipmentName;
        this.purposes = Cutlass.purposes;
        this.price = Cutlass.price;
    }
}
exports.Cutlass = Cutlass;
Cutlass.damage = new DiceRoll_1.DiceRoll(2, 4);
Cutlass.critical = new Critical_1.Critical(18);
Cutlass.equipmentName = EquipmentName_1.EquipmentName.cutlass;
Cutlass.purposes = [new WeaponPurpose_1.WeaponPurposeMelee()];
Cutlass.price = 75;
