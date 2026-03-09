"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.LightArmor = void 0;
const Proficiency_1 = require("../../../../../../Sheet/Proficiency");
const Armor_1 = require("../Armor");
class LightArmor extends Armor_1.Armor {
    constructor() {
        super(Proficiency_1.Proficiency.lightArmor);
    }
}
exports.LightArmor = LightArmor;
