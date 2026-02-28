"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Specialist = void 0;
const errors_1 = require("../../../../errors");
const Ability_1 = require("../../../Ability");
const RoleAbility_1 = require("../../RoleAbility");
const RoleAbilityName_1 = require("../../RoleAbilityName");
const SpecialistEffect_1 = require("./SpecialistEffect");
class Specialist extends RoleAbility_1.RoleAbility {
    constructor(skills) {
        super(RoleAbilityName_1.RoleAbilityName.specialist);
        this.effects = new Ability_1.AbilityEffects({
            triggered: {
                default: new SpecialistEffect_1.SpecialistEffect(skills),
            },
        });
    }
    addToSheet(transaction) {
        this.validateSkills(transaction.sheet);
        super.addToSheet(transaction);
    }
    getSkills() {
        return this.effects.triggered.default.getSkills();
    }
    validateSkills(sheet) {
        const { intelligence } = sheet.getSheetAttributes().getValues();
        const allowedSkills = intelligence > 0 ? intelligence : 1;
        if (this.getSkills().length !== allowedSkills) {
            throw new errors_1.SheetBuilderError('INVALID_SPECIALIST_SKILLS_SIZE');
        }
        const sheetSkills = sheet.getSheetSkills().getSkills();
        const isEverySkillTrained = this.getSkills()
            .every(specialistSkill => sheetSkills[specialistSkill].getIsTrained());
        if (!isEverySkillTrained) {
            throw new errors_1.SheetBuilderError('INVALID_SPECIALIST_SKILLS_NOT_TRAINED');
        }
    }
}
exports.Specialist = Specialist;
