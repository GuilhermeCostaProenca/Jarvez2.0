"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.StiffLeather = void 0;
const Ability_1 = require("../../Ability");
const RaceAbility_1 = require("../RaceAbility");
const RaceAbilityName_1 = require("../RaceAbilityName");
const StiffLeatherEffect_1 = require("./StiffLeatherEffect");
class StiffLeather extends RaceAbility_1.RaceAbility {
    constructor() {
        super(RaceAbilityName_1.RaceAbilityName.stiffLeather);
        this.effects = new Ability_1.AbilityEffects({
            passive: {
                default: new StiffLeatherEffect_1.StiffLeatherEffect(),
            },
        });
    }
}
exports.StiffLeather = StiffLeather;
