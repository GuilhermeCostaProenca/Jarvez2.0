"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Musket = void 0;
const Critical_1 = require("../../../../../Attack/Critical");
const DiceRoll_1 = require("../../../../../Dice/DiceRoll");
const EquipmentName_1 = require("../../../EquipmentName");
const FireArmWeapon_1 = require("./FireArmWeapon");
class Musket extends FireArmWeapon_1.FireArmWeapon {
    constructor() {
        super(...arguments);
        this.damage = Musket.damage;
        this.critical = Musket.critical;
        this.name = Musket.equipmentName;
        this.price = Musket.price;
    }
}
exports.Musket = Musket;
Musket.damage = new DiceRoll_1.DiceRoll(2, 8);
Musket.critical = new Critical_1.Critical(19, 3);
Musket.equipmentName = EquipmentName_1.EquipmentName.musket;
Musket.price = 500;
