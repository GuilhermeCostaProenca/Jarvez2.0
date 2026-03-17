"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DruidSpellsEffect = void 0;
const Sheet_1 = require("../../../Sheet");
const Spell_1 = require("../../../Spell");
const RoleAbilityName_1 = require("../../RoleAbilityName");
const SpellsAbilityEffect_1 = require("../../SpellsAbilityEffect");
class DruidSpellsEffect extends SpellsAbilityEffect_1.SpellsAbilityEffect {
    constructor(spells, schools) {
        super(spells, 2, RoleAbilityName_1.RoleAbilityName.druidSpells, schools);
        this.spellType = 'divine';
        this.spellsLearnFrequency = 'even';
        this.spellsAttribute = 'wisdom';
        this.circleLearnLevel = {
            [Spell_1.SpellCircle.first]: Sheet_1.Level.one,
            [Spell_1.SpellCircle.second]: Sheet_1.Level.six,
        };
        this.description = 'Escolha três escolas de magia. Uma vez'
            + ' feita, essa escolha não pode ser mudada. Você pode'
            + ' lançar magias divinas de 1º círculo que pertençam a'
            + ' essas escolas. À medida que sobe de nível, pode lançar'
            + ' magias de círculos maiores (2º círculo no 6º nível,'
            + ' 3º círculo no 10º nível e 4º círculo no 14º nível).';
    }
}
exports.DruidSpellsEffect = DruidSpellsEffect;
