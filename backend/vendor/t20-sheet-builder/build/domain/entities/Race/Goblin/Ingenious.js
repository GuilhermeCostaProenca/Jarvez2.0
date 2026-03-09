"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Ingenious = void 0;
const Ability_1 = require("../../Ability");
const RaceAbility_1 = require("../RaceAbility");
const RaceAbilityName_1 = require("../RaceAbilityName");
const IngeniousEffect_1 = require("./IngeniousEffect");
class Ingenious extends RaceAbility_1.RaceAbility {
    constructor() {
        super(RaceAbilityName_1.RaceAbilityName.ingenious);
        this.effects = new Ability_1.AbilityEffects({
            passive: {
                default: new IngeniousEffect_1.IngeniousEffect(),
            },
        });
    }
}
exports.Ingenious = Ingenious;
