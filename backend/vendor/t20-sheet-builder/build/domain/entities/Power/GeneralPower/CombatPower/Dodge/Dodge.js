"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Dodge = void 0;
const AbilityEffects_1 = require("../../../../Ability/AbilityEffects");
const DodgeEffect_1 = require("./DodgeEffect");
const GeneralPower_1 = require("../../GeneralPower");
const GeneralPowerName_1 = require("../../GeneralPowerName");
const AttributeRequirement_1 = require("../../../Requirement/AttributeRequirement");
const GeneralPowerGroup_1 = require("../../GeneralPowerGroup");
const AbilityEffectsStatic_1 = require("../../../../Ability/AbilityEffectsStatic");
class Dodge extends GeneralPower_1.GeneralPower {
    constructor() {
        super(GeneralPowerName_1.GeneralPowerName.dodge);
        this.group = GeneralPowerGroup_1.GeneralPowerGroup.combat;
        this.effects = new AbilityEffects_1.AbilityEffects({
            passive: {
                default: new DodgeEffect_1.DodgeEffect(),
            },
        });
        super.addRequirement(Dodge.requirement);
    }
}
exports.Dodge = Dodge;
Dodge.powerName = GeneralPowerName_1.GeneralPowerName.dodge;
Dodge.effects = new AbilityEffectsStatic_1.AbilityEffectsStatic({
    passive: {
        default: DodgeEffect_1.DodgeEffect,
    },
});
Dodge.requirement = new AttributeRequirement_1.AttributeRequirement('dexterity', 1);
