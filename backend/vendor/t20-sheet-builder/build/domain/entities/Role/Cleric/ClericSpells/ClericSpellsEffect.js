"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ClericSpellsEffect = void 0;
const Spell_1 = require("../../../Spell");
const RoleAbilityName_1 = require("../../RoleAbilityName");
const SpellsAbilityEffect_1 = require("../../SpellsAbilityEffect");
class ClericSpellsEffect extends SpellsAbilityEffect_1.SpellsAbilityEffect {
    constructor(spells) {
        super(spells, 3, RoleAbilityName_1.RoleAbilityName.clericSpells);
        this.spellType = 'divine';
        this.spellsLearnFrequency = 'all';
        this.spellsAttribute = 'wisdom';
        this.circleLearnLevel = {
            [Spell_1.SpellCircle.first]: 1,
            [Spell_1.SpellCircle.second]: 5,
        };
        this.description = 'Você pode lançar magias divinas de 1º'
            + ' círculo. A cada quatro níveis, pode lançar magias de'
            + ' um círculo maior (2º círculo no 5º nível, 3º círculo'
            + ' no 9º nível e assim por diante).';
    }
}
exports.ClericSpellsEffect = ClericSpellsEffect;
