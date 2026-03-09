"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.HeavyArmor = void 0;
const Proficiency_1 = require("../../../../../../Sheet/Proficiency");
const Armor_1 = require("../Armor");
class HeavyArmor extends Armor_1.Armor {
    constructor() {
        super(Proficiency_1.Proficiency.heavyArmor);
    }
}
exports.HeavyArmor = HeavyArmor;
