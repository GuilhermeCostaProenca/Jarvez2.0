"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Medicine = void 0;
const AbilityEffects_1 = require("../../../../Ability/AbilityEffects");
const AbilityEffectsStatic_1 = require("../../../../Ability/AbilityEffectsStatic");
const SkillName_1 = require("../../../../Skill/SkillName");
const AttributeRequirement_1 = require("../../../Requirement/AttributeRequirement");
const SkillRequirement_1 = require("../../../Requirement/SkillRequirement");
const GeneralPower_1 = require("../../GeneralPower");
const GeneralPowerGroup_1 = require("../../GeneralPowerGroup");
const GeneralPowerName_1 = require("../../GeneralPowerName");
const MedicineEffect_1 = require("./MedicineEffect");
class Medicine extends GeneralPower_1.GeneralPower {
    constructor() {
        super(GeneralPowerName_1.GeneralPowerName.medicine);
        this.group = GeneralPowerGroup_1.GeneralPowerGroup.destiny;
        this.effects = new AbilityEffects_1.AbilityEffects({
            activateable: {
                default: new MedicineEffect_1.MedicineEffect(),
            },
        });
        this.addRequirement(Medicine.wisdomRequirement);
        this.addRequirement(Medicine.cureRequirement);
    }
}
exports.Medicine = Medicine;
Medicine.powerName = GeneralPowerName_1.GeneralPowerName.medicine;
Medicine.effects = new AbilityEffectsStatic_1.AbilityEffectsStatic({
    activateable: {
        default: MedicineEffect_1.MedicineEffect,
    },
});
Medicine.wisdomRequirement = new AttributeRequirement_1.AttributeRequirement('wisdom', 1);
Medicine.cureRequirement = new SkillRequirement_1.SkillRequirement(SkillName_1.SkillName.cure);
