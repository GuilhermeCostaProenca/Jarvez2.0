"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.FlamesExplosion = void 0;
const AbilityEffects_1 = require("../../Ability/AbilityEffects");
const Spell_1 = require("../Spell");
const SpellCircle_1 = require("../SpellCircle");
const SpellName_1 = require("../SpellName");
const SpellSchool_1 = require("../SpellSchool");
const FlamesExplosionDefaultEffect_1 = require("./FlamesExplosionDefaultEffect");
class FlamesExplosion extends Spell_1.Spell {
    constructor() {
        super(FlamesExplosion.spellName, FlamesExplosion.circle, 'arcane');
        this.shortDescription = FlamesExplosion.shortDescription;
        this.effects = new AbilityEffects_1.AbilityEffects({
            activateable: {
                default: new FlamesExplosionDefaultEffect_1.FlamesExplosionDefaultEffect(),
            },
        });
        this.school = FlamesExplosion.school;
    }
}
exports.FlamesExplosion = FlamesExplosion;
FlamesExplosion.circle = SpellCircle_1.SpellCircle.first;
FlamesExplosion.school = SpellSchool_1.SpellSchool.evocation;
FlamesExplosion.spellName = SpellName_1.SpellName.flamesExplosion;
FlamesExplosion.shortDescription = 'Cone causa dano de fogo.';
FlamesExplosion.spellType = 'arcane';
