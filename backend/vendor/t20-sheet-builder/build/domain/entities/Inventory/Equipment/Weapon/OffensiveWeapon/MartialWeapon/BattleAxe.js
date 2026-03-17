"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.BattleAxe = void 0;
const Critical_1 = require("../../../../../Attack/Critical");
const DiceRoll_1 = require("../../../../../Dice/DiceRoll");
const EquipmentName_1 = require("../../../EquipmentName");
const WeaponPurpose_1 = require("../../WeaponPurpose");
const MartialWeapon_1 = require("./MartialWeapon");
class BattleAxe extends MartialWeapon_1.MartialWeapon {
    constructor() {
        super(...arguments);
        this.damage = BattleAxe.damage;
        this.critical = BattleAxe.critical;
        this.name = BattleAxe.equipmentName;
        this.purposes = BattleAxe.purposes;
        this.price = BattleAxe.price;
    }
}
exports.BattleAxe = BattleAxe;
BattleAxe.damage = new DiceRoll_1.DiceRoll(1, 8);
BattleAxe.critical = new Critical_1.Critical(20, 3);
BattleAxe.equipmentName = EquipmentName_1.EquipmentName.battleAxe;
BattleAxe.purposes = [new WeaponPurpose_1.WeaponPurposeMelee()];
BattleAxe.price = 10;
