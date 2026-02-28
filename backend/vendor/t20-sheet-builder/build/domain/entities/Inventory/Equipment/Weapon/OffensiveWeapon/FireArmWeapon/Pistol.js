"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Pistol = void 0;
const Critical_1 = require("../../../../../Attack/Critical");
const DiceRoll_1 = require("../../../../../Dice/DiceRoll");
const EquipmentName_1 = require("../../../EquipmentName");
const FireArmWeapon_1 = require("./FireArmWeapon");
class Pistol extends FireArmWeapon_1.FireArmWeapon {
    constructor() {
        super(...arguments);
        this.damage = Pistol.damage;
        this.critical = Pistol.critical;
        this.name = Pistol.equipmentName;
        this.price = Pistol.price;
    }
}
exports.Pistol = Pistol;
Pistol.damage = new DiceRoll_1.DiceRoll(2, 6);
Pistol.critical = new Critical_1.Critical(19, 3);
Pistol.equipmentName = EquipmentName_1.EquipmentName.pistol;
Pistol.price = 250;
