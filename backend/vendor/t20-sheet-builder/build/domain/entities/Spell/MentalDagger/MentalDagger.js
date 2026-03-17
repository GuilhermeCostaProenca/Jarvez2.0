"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.MentalDagger = void 0;
const AbilityEffects_1 = require("../../Ability/AbilityEffects");
const Spell_1 = require("../Spell");
const SpellCircle_1 = require("../SpellCircle");
const SpellName_1 = require("../SpellName");
const SpellSchool_1 = require("../SpellSchool");
const MentalDaggerDefaultEffect_1 = require("./MentalDaggerDefaultEffect");
class MentalDagger extends Spell_1.Spell {
    constructor() {
        super(MentalDagger.spellName, MentalDagger.circle, 'arcane');
        this.school = MentalDagger.school;
        this.shortDescription = MentalDagger.shortDescription;
        this.effects = new AbilityEffects_1.AbilityEffects({
            activateable: {
                default: new MentalDaggerDefaultEffect_1.MentalDaggerDefaultEffect(),
            },
        });
    }
}
exports.MentalDagger = MentalDagger;
MentalDagger.circle = SpellCircle_1.SpellCircle.first;
MentalDagger.spellName = SpellName_1.SpellName.mentalDagger;
MentalDagger.school = SpellSchool_1.SpellSchool.enchantment;
MentalDagger.shortDescription = 'Alvo sofre dano psíquico e pode ficar atordoado.';
MentalDagger.spellType = 'arcane';
