"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Shield = void 0;
const Proficiency_1 = require("../../../../../Sheet/Proficiency");
const EquipmentImprovementCategory_1 = require("../../../EquipmentImprovement/EquipmentImprovementCategory");
const DefensiveWeapon_1 = require("../DefensiveWeapon");
class Shield extends DefensiveWeapon_1.DefensiveWeapon {
    get isWieldable() {
        return true;
    }
    constructor() {
        super(Proficiency_1.Proficiency.shield);
        this.categoryForImprovement = EquipmentImprovementCategory_1.EquipmentImprovementCategory.armorAndShield;
    }
}
exports.Shield = Shield;
