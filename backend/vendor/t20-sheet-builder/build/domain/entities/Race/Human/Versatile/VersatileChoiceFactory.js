"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.VersatileChoiceFactory = void 0;
const SheetBuilderError_1 = require("../../../../errors/SheetBuilderError");
const Power_1 = require("../../../Power");
const Skill_1 = require("../../../Skill");
const VersatileChoicePower_1 = require("./VersatileChoicePower");
const VersatileChoiceSkill_1 = require("./VersatileChoiceSkill");
class VersatileChoiceFactory {
    static make(type, choice) {
        if (type === 'skill') {
            return VersatileChoiceFactory.makeVersatileChoiceSkill(choice);
        }
        return VersatileChoiceFactory.makeVersatileChoicePower(choice);
    }
    static makeVersatileChoiceSkill(choice) {
        if (!VersatileChoiceFactory.isSkill(choice)) {
            throw new SheetBuilderError_1.SheetBuilderError('INVALID_SKILL_CHOICE');
        }
        return new VersatileChoiceSkill_1.VersatileChoiceSkill(choice);
    }
    static makeVersatileChoicePower(choice) {
        if (!VersatileChoiceFactory.isPower(choice)) {
            throw new SheetBuilderError_1.SheetBuilderError('INVALID_POWER_CHOICE');
        }
        const power = Power_1.GeneralPowerFactory.make({ name: choice });
        return new VersatileChoicePower_1.VersatileChoicePower(power);
    }
    static isPower(choice) {
        return choice in Power_1.GeneralPowerName;
    }
    static isSkill(choice) {
        return choice in Skill_1.SkillName;
    }
}
exports.VersatileChoiceFactory = VersatileChoiceFactory;
