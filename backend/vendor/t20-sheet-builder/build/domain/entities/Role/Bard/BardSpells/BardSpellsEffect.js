"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.BardSpellsEffect = void 0;
const Sheet_1 = require("../../../Sheet");
const Spell_1 = require("../../../Spell");
const RoleAbilityName_1 = require("../../RoleAbilityName");
const SpellsAbilityEffect_1 = require("../../SpellsAbilityEffect");
class BardSpellsEffect extends SpellsAbilityEffect_1.SpellsAbilityEffect {
    constructor(schools, spells) {
        super(spells, 2, RoleAbilityName_1.RoleAbilityName.bardSpells, schools);
        this.spellType = 'arcane';
        this.spellsLearnFrequency = 'even';
        this.spellsAttribute = 'charisma';
        this.circleLearnLevel = {
            [Spell_1.SpellCircle.first]: Sheet_1.Level.one,
            [Spell_1.SpellCircle.second]: Sheet_1.Level.six,
        };
        this.description = 'Escolha três escolas de magia. Você pode'
            + ' lançar magias arcanas de 1º círculo que pertençam a'
            + ' essas escolas.';
    }
}
exports.BardSpellsEffect = BardSpellsEffect;
