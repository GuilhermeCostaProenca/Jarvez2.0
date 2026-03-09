"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AllihannaArmor = void 0;
const Ability_1 = require("../../Ability");
const RaceAbility_1 = require("../RaceAbility");
const RaceAbilityName_1 = require("../RaceAbilityName");
const AllihannaArmorEffect_1 = require("./AllihannaArmorEffect");
class AllihannaArmor extends RaceAbility_1.RaceAbility {
    constructor() {
        super(RaceAbilityName_1.RaceAbilityName.allihannaArmor);
        this.effects = new Ability_1.AbilityEffects({
            activateable: {
                default: new AllihannaArmorEffect_1.AllihannaArmorEffect(),
            },
        });
    }
}
exports.AllihannaArmor = AllihannaArmor;
