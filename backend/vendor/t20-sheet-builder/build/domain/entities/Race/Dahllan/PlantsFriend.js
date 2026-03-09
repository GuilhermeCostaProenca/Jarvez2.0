"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.PlantsFriend = void 0;
const Ability_1 = require("../../Ability");
const RaceAbility_1 = require("../RaceAbility");
const RaceAbilityName_1 = require("../RaceAbilityName");
const PlantsFriendEffect_1 = require("./PlantsFriendEffect");
class PlantsFriend extends RaceAbility_1.RaceAbility {
    constructor() {
        super(RaceAbilityName_1.RaceAbilityName.plantsFriend);
        this.effects = new Ability_1.AbilityEffects({
            passive: {
                default: new PlantsFriendEffect_1.PlantsFriendEffect(),
            },
        });
    }
}
exports.PlantsFriend = PlantsFriend;
