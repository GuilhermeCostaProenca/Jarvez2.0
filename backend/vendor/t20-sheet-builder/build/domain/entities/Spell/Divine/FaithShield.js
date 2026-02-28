"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.FaithShield = void 0;
const Ability_1 = require("../../Ability");
const Spell_1 = require("../Spell");
const SpellCircle_1 = require("../SpellCircle");
const SpellName_1 = require("../SpellName");
const SpellSchool_1 = require("../SpellSchool");
class FaithShield extends Spell_1.Spell {
    constructor() {
        super(SpellName_1.SpellName.faithShield, SpellCircle_1.SpellCircle.first, 'divine');
        this.school = FaithShield.school;
        this.shortDescription = 'Protege uma criatura.';
        this.effects = new Ability_1.AbilityEffects();
    }
}
exports.FaithShield = FaithShield;
FaithShield.circle = SpellCircle_1.SpellCircle.first;
FaithShield.school = SpellSchool_1.SpellSchool.abjuration;
FaithShield.spellName = SpellName_1.SpellName.faithShield;
FaithShield.shortDescription = 'Alvo recebe bônus em testes de resistência.';
FaithShield.spellType = 'divine';
