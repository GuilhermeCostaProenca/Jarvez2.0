"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Deformity = void 0;
const AbilityEffects_1 = require("../../../Ability/AbilityEffects");
const RaceAbility_1 = require("../../RaceAbility");
const RaceAbilityName_1 = require("../../RaceAbilityName");
const DeformityEffect_1 = require("./DeformityEffect");
class Deformity extends RaceAbility_1.RaceAbility {
    constructor() {
        super(RaceAbilityName_1.RaceAbilityName.deformity);
        this.effects = new AbilityEffects_1.AbilityEffects({
            passive: {
                default: new DeformityEffect_1.DeformityEffect(),
            },
        });
    }
    addDeformity(choices) {
        this.effects.passive.default.addChoice(choices);
    }
    serializeChoices() {
        return this.effects.passive.default.choices.map(choice => ({
            type: 'skill',
            name: choice,
        }));
    }
}
exports.Deformity = Deformity;
