"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.OffensiveWeapon = void 0;
const Weapon_1 = require("../Weapon");
const EquipmentImprovementCategory_1 = require("../../EquipmentImprovement/EquipmentImprovementCategory");
class OffensiveWeapon extends Weapon_1.Weapon {
    constructor() {
        super(...arguments);
        this.categoryForImprovement = EquipmentImprovementCategory_1.EquipmentImprovementCategory.weapon;
    }
    get isWieldable() {
        return true;
    }
    get type() {
        return 'offensive';
    }
}
exports.OffensiveWeapon = OffensiveWeapon;
