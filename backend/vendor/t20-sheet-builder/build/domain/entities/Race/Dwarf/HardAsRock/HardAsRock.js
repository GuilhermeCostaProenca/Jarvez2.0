"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.HardAsRock = void 0;
const AbilityEffects_1 = require("../../../Ability/AbilityEffects");
const RaceAbility_1 = require("../../RaceAbility");
const RaceAbilityName_1 = require("../../RaceAbilityName");
const HardAsRockInitialEffect_1 = require("./HardAsRockInitialEffect");
const HardAsRockPerLevelEffect_1 = require("./HardAsRockPerLevelEffect");
class HardAsRock extends RaceAbility_1.RaceAbility {
    constructor() {
        super(RaceAbilityName_1.RaceAbilityName.hardAsRock);
        this.effects = new AbilityEffects_1.AbilityEffects({
            passive: {
                initial: new HardAsRockInitialEffect_1.HardAsRockInitialEffect(),
                perLevel: new HardAsRockPerLevelEffect_1.HardAsRockPerLevelEffect(),
            },
        });
    }
}
exports.HardAsRock = HardAsRock;
