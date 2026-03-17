"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.HeredrimmTradition = void 0;
const Ability_1 = require("../../../Ability");
const RaceAbility_1 = require("../../RaceAbility");
const RaceAbilityName_1 = require("../../RaceAbilityName");
const HeredrimmTraditionEffect_1 = require("./HeredrimmTraditionEffect");
class HeredrimmTradition extends RaceAbility_1.RaceAbility {
    constructor() {
        super(RaceAbilityName_1.RaceAbilityName.heredrimmTradition);
        this.effects = new Ability_1.AbilityEffects({
            passive: {
                default: new HeredrimmTraditionEffect_1.HeredrimmTraditionEffect(),
            },
        });
    }
}
exports.HeredrimmTradition = HeredrimmTradition;
