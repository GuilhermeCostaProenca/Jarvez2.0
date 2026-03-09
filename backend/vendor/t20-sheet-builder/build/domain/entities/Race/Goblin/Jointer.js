"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Jointer = void 0;
const Ability_1 = require("../../Ability");
const RaceAbility_1 = require("../RaceAbility");
const RaceAbilityName_1 = require("../RaceAbilityName");
const JointerEffect_1 = require("./JointerEffect");
class Jointer extends RaceAbility_1.RaceAbility {
    constructor() {
        super(RaceAbilityName_1.RaceAbilityName.jointer);
        this.effects = new Ability_1.AbilityEffects({
            passive: {
                default: new JointerEffect_1.JointerEffect(),
            },
        });
    }
}
exports.Jointer = Jointer;
