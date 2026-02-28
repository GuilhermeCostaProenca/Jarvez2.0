"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.MagicBlood = void 0;
const Ability_1 = require("../../Ability");
const RaceAbility_1 = require("../RaceAbility");
const RaceAbilityName_1 = require("../RaceAbilityName");
const MagicBloodEffect_1 = require("./MagicBloodEffect");
class MagicBlood extends RaceAbility_1.RaceAbility {
    constructor() {
        super(RaceAbilityName_1.RaceAbilityName.magicBlood);
        this.effects = new Ability_1.AbilityEffects({
            passive: {
                default: new MagicBloodEffect_1.MagicBloodEffect(),
            },
        });
    }
}
exports.MagicBlood = MagicBlood;
