"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.MysticTattoo = void 0;
const Ability_1 = require("../../../Ability");
const RaceAbility_1 = require("../../RaceAbility");
const RaceAbilityName_1 = require("../../RaceAbilityName");
const MysticTattooEffect_1 = require("./MysticTattooEffect");
class MysticTattoo extends RaceAbility_1.RaceAbility {
    constructor(spell) {
        super(RaceAbilityName_1.RaceAbilityName.mysticTattoo);
        this.spell = spell;
        this.effects = new Ability_1.AbilityEffects({
            passive: {
                default: new MysticTattooEffect_1.MysticTattooEffect(spell),
            },
        });
    }
}
exports.MysticTattoo = MysticTattoo;
