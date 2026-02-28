"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Scimitar = void 0;
const Critical_1 = require("../../../../../Attack/Critical");
const DiceRoll_1 = require("../../../../../Dice/DiceRoll");
const EquipmentName_1 = require("../../../EquipmentName");
const MartialWeapon_1 = require("./MartialWeapon");
class Scimitar extends MartialWeapon_1.MartialWeapon {
    constructor() {
        super(...arguments);
        this.damage = Scimitar.damage;
        this.critical = Scimitar.critical;
        this.name = Scimitar.equipmentName;
        this.purposes = Scimitar.purposes;
        this.price = Scimitar.price;
    }
}
exports.Scimitar = Scimitar;
Scimitar.damage = new DiceRoll_1.DiceRoll(1, 6);
Scimitar.critical = new Critical_1.Critical(18);
Scimitar.equipmentName = EquipmentName_1.EquipmentName.scimitar;
Scimitar.purposes = [];
Scimitar.price = 15;
