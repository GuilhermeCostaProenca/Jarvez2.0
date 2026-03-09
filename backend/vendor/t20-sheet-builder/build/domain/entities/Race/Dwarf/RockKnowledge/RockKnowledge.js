"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.RockKnowledge = void 0;
const AbilityEffects_1 = require("../../../Ability/AbilityEffects");
const RaceAbility_1 = require("../../RaceAbility");
const RaceAbilityName_1 = require("../../RaceAbilityName");
const RockKnowledgeEffect_1 = require("./RockKnowledgeEffect");
class RockKnowledge extends RaceAbility_1.RaceAbility {
    constructor() {
        super(RaceAbilityName_1.RaceAbilityName.rockKnowledge);
        this.effects = new AbilityEffects_1.AbilityEffects({
            passive: {
                default: new RockKnowledgeEffect_1.RockKnowledgeEffect(),
            },
        });
    }
}
exports.RockKnowledge = RockKnowledge;
