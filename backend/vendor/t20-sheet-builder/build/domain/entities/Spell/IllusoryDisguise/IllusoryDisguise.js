"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.IllusoryDisguise = void 0;
const AbilityEffects_1 = require("../../Ability/AbilityEffects");
const Spell_1 = require("../Spell");
const SpellCircle_1 = require("../SpellCircle");
const SpellName_1 = require("../SpellName");
const SpellSchool_1 = require("../SpellSchool");
const IllusoryDisguiseDefaultEffect_1 = require("./IllusoryDisguiseDefaultEffect");
class IllusoryDisguise extends Spell_1.Spell {
    constructor() {
        super(IllusoryDisguise.spellName, IllusoryDisguise.circle, 'arcane');
        this.shortDescription = IllusoryDisguise.shortDescription;
        this.effects = new AbilityEffects_1.AbilityEffects({
            activateable: {
                default: new IllusoryDisguiseDefaultEffect_1.IllusoryDisguiseDefaultEffect(),
            },
        });
        this.school = IllusoryDisguise.school;
    }
}
exports.IllusoryDisguise = IllusoryDisguise;
IllusoryDisguise.spellName = SpellName_1.SpellName.illusoryDisguise;
IllusoryDisguise.circle = SpellCircle_1.SpellCircle.first;
IllusoryDisguise.school = SpellSchool_1.SpellSchool.illusion;
IllusoryDisguise.shortDescription = 'Muda a aparência de uma ou mais criaturas.';
IllusoryDisguise.spellType = 'arcane';
