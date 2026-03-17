"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DivineProtection = void 0;
const Ability_1 = require("../../Ability");
const Spell_1 = require("../Spell");
const SpellCircle_1 = require("../SpellCircle");
const SpellName_1 = require("../SpellName");
const SpellSchool_1 = require("../SpellSchool");
class DivineProtection extends Spell_1.Spell {
    constructor() {
        super(SpellName_1.SpellName.divineProtection, SpellCircle_1.SpellCircle.first, DivineProtection.spellType);
        this.school = DivineProtection.school;
        this.shortDescription = DivineProtection.shortDescription;
        this.effects = new Ability_1.AbilityEffects();
    }
}
exports.DivineProtection = DivineProtection;
DivineProtection.circle = SpellCircle_1.SpellCircle.first;
DivineProtection.school = SpellSchool_1.SpellSchool.abjuration;
DivineProtection.spellName = SpellName_1.SpellName.divineProtection;
DivineProtection.shortDescription = 'Alvo recebe bônus em testes de resistência.';
DivineProtection.spellType = 'divine';
