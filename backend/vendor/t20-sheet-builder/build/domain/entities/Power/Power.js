"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Power = void 0;
const UnfulfilledRequirementError_1 = require("../../errors/UnfulfilledRequirementError");
const Ability_1 = require("../Ability/Ability");
class Power extends Ability_1.Ability {
    constructor(name, powerType) {
        super(name, 'power');
        this.name = name;
        this.powerType = powerType;
        this.requirements = [];
    }
    verifyRequirements(sheet) {
        const requirementNotMet = this.requirements.find(requirement => !requirement.verify(sheet));
        if (requirementNotMet) {
            throw new UnfulfilledRequirementError_1.UnfulfilledRequirementError(requirementNotMet);
        }
    }
    addRequirement(requirement) {
        this.requirements.push(requirement);
    }
}
exports.Power = Power;
