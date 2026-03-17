"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SheetProficiencies = void 0;
const Proficiency_1 = require("./Proficiency");
class SheetProficiencies {
    constructor(proficiencies = new Set([Proficiency_1.Proficiency.simple, Proficiency_1.Proficiency.lightArmor])) {
        this.proficiencies = proficiencies;
    }
    addProficiency(proficiency) {
        this.proficiencies.add(proficiency);
    }
    has(proficiency) {
        return this.proficiencies.has(proficiency);
    }
    getProficiencies() {
        return Array.from(this.proficiencies);
    }
}
exports.SheetProficiencies = SheetProficiencies;
