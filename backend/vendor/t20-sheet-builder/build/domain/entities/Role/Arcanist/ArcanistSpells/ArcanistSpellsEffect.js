"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArcanistSpellsEffect = void 0;
const Level_1 = require("../../../Sheet/Level");
const SpellCircle_1 = require("../../../Spell/SpellCircle");
const RoleAbilityName_1 = require("../../RoleAbilityName");
const SpellsAbilityEffect_1 = require("../../SpellsAbilityEffect");
class ArcanistSpellsEffect extends SpellsAbilityEffect_1.SpellsAbilityEffect {
    get description() {
        return 'Você pode lançar magias arcanas de 1º	círculo e começa com três magias de 1º círculo.';
    }
    constructor(spells, learnFrequency, attribute) {
        super(spells, 3, RoleAbilityName_1.RoleAbilityName.arcanistSpells);
        this.circleLearnLevel = {
            [SpellCircle_1.SpellCircle.first]: Level_1.Level.one,
            [SpellCircle_1.SpellCircle.second]: Level_1.Level.five,
        };
        this.spellType = 'arcane';
        this.spellsLearnFrequency = learnFrequency;
        this.spellsAttribute = attribute;
    }
}
exports.ArcanistSpellsEffect = ArcanistSpellsEffect;
