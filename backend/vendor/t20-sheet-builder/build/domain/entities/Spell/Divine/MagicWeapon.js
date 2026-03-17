"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.MagicWeapon = void 0;
const Ability_1 = require("../../Ability");
const Spell_1 = require("../Spell");
const SpellCircle_1 = require("../SpellCircle");
const SpellName_1 = require("../SpellName");
const SpellSchool_1 = require("../SpellSchool");
class MagicWeapon extends Spell_1.Spell {
    constructor() {
        super(SpellName_1.SpellName.magicWeapon, SpellCircle_1.SpellCircle.first, 'divine');
        this.school = MagicWeapon.school;
        this.shortDescription = MagicWeapon.shortDescription;
        this.effects = new Ability_1.AbilityEffects();
    }
}
exports.MagicWeapon = MagicWeapon;
MagicWeapon.circle = SpellCircle_1.SpellCircle.first;
MagicWeapon.school = SpellSchool_1.SpellSchool.transmutation;
MagicWeapon.spellName = SpellName_1.SpellName.magicWeapon;
MagicWeapon.shortDescription = 'Alvo recebe bônus em testes de resistência.';
MagicWeapon.spellType = 'divine';
