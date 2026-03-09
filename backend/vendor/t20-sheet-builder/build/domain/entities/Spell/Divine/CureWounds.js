"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.CureWounds = void 0;
const Ability_1 = require("../../Ability");
const Spell_1 = require("../Spell");
const SpellCircle_1 = require("../SpellCircle");
const SpellName_1 = require("../SpellName");
const SpellSchool_1 = require("../SpellSchool");
class CureWounds extends Spell_1.Spell {
    constructor() {
        super(SpellName_1.SpellName.cureWounds, CureWounds.circle, 'divine');
        this.school = CureWounds.school;
        this.shortDescription = CureWounds.shortDescription;
        this.effects = new Ability_1.AbilityEffects();
    }
}
exports.CureWounds = CureWounds;
CureWounds.circle = SpellCircle_1.SpellCircle.first;
CureWounds.school = SpellSchool_1.SpellSchool.evocation;
CureWounds.spellName = SpellName_1.SpellName.cureWounds;
CureWounds.shortDescription = 'Seu toque recupera pontos de vida.';
CureWounds.spellType = 'divine';
