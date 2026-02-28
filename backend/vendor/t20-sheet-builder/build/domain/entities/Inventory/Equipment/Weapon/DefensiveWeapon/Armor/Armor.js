"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Armor = void 0;
const EquipmentImprovementCategory_1 = require("../../../EquipmentImprovement/EquipmentImprovementCategory");
const DefensiveWeapon_1 = require("../DefensiveWeapon");
class Armor extends DefensiveWeapon_1.DefensiveWeapon {
    get isWieldable() {
        return false;
    }
    constructor(proficiency) {
        super(proficiency);
        this.proficiency = proficiency;
        this.categoryForImprovement = EquipmentImprovementCategory_1.EquipmentImprovementCategory.armorAndShield;
    }
}
exports.Armor = Armor;
