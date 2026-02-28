"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArcaneArmor = void 0;
const AbilityEffects_1 = require("../../Ability/AbilityEffects");
const Spell_1 = require("../Spell");
const SpellCircle_1 = require("../SpellCircle");
const SpellName_1 = require("../SpellName");
const SpellSchool_1 = require("../SpellSchool");
const ArcaneArmorDefaultEffect_1 = require("./ArcaneArmorDefaultEffect");
class ArcaneArmor extends Spell_1.Spell {
    constructor() {
        super(ArcaneArmor.spellName, ArcaneArmor.circle, 'arcane');
        this.shortDescription = ArcaneArmor.shortDescription;
        this.effects = new AbilityEffects_1.AbilityEffects({
            activateable: {
                default: new ArcaneArmorDefaultEffect_1.ArcaneArmorDefaultEffect(),
            },
        });
        this.school = ArcaneArmor.school;
    }
}
exports.ArcaneArmor = ArcaneArmor;
ArcaneArmor.circle = SpellCircle_1.SpellCircle.first;
ArcaneArmor.school = SpellSchool_1.SpellSchool.abjuration;
ArcaneArmor.spellName = SpellName_1.SpellName.arcaneArmor;
ArcaneArmor.shortDescription = 'Aumenta sua Defesa.';
ArcaneArmor.spellType = 'arcane';
