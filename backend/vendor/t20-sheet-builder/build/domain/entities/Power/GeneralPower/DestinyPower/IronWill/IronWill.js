"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.IronWill = void 0;
const AbilityEffects_1 = require("../../../../Ability/AbilityEffects");
const GeneralPower_1 = require("../../GeneralPower");
const GeneralPowerName_1 = require("../../GeneralPowerName");
const IronWillEffect_1 = require("./IronWillEffect");
const AttributeRequirement_1 = require("../../../Requirement/AttributeRequirement");
const GeneralPowerGroup_1 = require("../../GeneralPowerGroup");
const AbilityEffectsStatic_1 = require("../../../../Ability/AbilityEffectsStatic");
class IronWill extends GeneralPower_1.GeneralPower {
    constructor() {
        super(GeneralPowerName_1.GeneralPowerName.ironWill);
        this.group = GeneralPowerGroup_1.GeneralPowerGroup.destiny;
        this.effects = new AbilityEffects_1.AbilityEffects({
            passive: {
                default: new IronWillEffect_1.IronWillEffect(this.name),
            },
        });
        this.addRequirement(new AttributeRequirement_1.AttributeRequirement('wisdom', 1));
    }
}
exports.IronWill = IronWill;
IronWill.powerName = GeneralPowerName_1.GeneralPowerName.ironWill;
IronWill.effects = new AbilityEffectsStatic_1.AbilityEffectsStatic({
    passive: {
        default: IronWillEffect_1.IronWillEffect,
    },
});
