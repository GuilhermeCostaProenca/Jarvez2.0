"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ElvenSenses = void 0;
const Ability_1 = require("../../Ability");
const RaceAbility_1 = require("../RaceAbility");
const RaceAbilityName_1 = require("../RaceAbilityName");
const ElvenSensesEffect_1 = require("./ElvenSensesEffect");
class ElvenSenses extends RaceAbility_1.RaceAbility {
    constructor() {
        super(RaceAbilityName_1.RaceAbilityName.elvenSenses);
        this.effects = new Ability_1.AbilityEffects({
            passive: {
                default: new ElvenSensesEffect_1.ElvenSensesEffect(),
            },
        });
    }
}
exports.ElvenSenses = ElvenSenses;
