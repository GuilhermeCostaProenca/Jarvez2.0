"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Spells = void 0;
const ControlPlants_1 = require("./ControlPlants/ControlPlants");
const ArcaneArmor_1 = require("./ArcaneArmor/ArcaneArmor");
const FlamesExplosion_1 = require("./FlamesExplosion/FlamesExplosion");
const IllusoryDisguise_1 = require("./IllusoryDisguise/IllusoryDisguise");
const MentalDagger_1 = require("./MentalDagger/MentalDagger");
const CureWounds_1 = require("./Divine/CureWounds");
const DivineProtection_1 = require("./Divine/DivineProtection");
const FaithShield_1 = require("./Divine/FaithShield");
const MagicWeapon_1 = require("./Divine/MagicWeapon");
class Spells {
    static getAll() {
        return [
            ...Spells.getAllArcane(),
            ...Spells.getAllDivine(),
        ];
    }
    static getAllArcane() {
        return [
            ArcaneArmor_1.ArcaneArmor,
            FlamesExplosion_1.FlamesExplosion,
            IllusoryDisguise_1.IllusoryDisguise,
            MentalDagger_1.MentalDagger,
            ControlPlants_1.ControlPlants,
        ];
    }
    static getAllDivine() {
        return [
            CureWounds_1.CureWounds,
            DivineProtection_1.DivineProtection,
            FaithShield_1.FaithShield,
            MagicWeapon_1.MagicWeapon,
        ];
    }
    static getBySchool(school) {
        return Spells.getAll().filter(spell => spell.school === school);
    }
}
exports.Spells = Spells;
