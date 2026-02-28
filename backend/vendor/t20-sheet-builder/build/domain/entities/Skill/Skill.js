"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Skill = void 0;
const SheetBuilderError_1 = require("../../errors/SheetBuilderError");
const ContextualModifierList_1 = require("../Modifier/ContextualModifier/ContextualModifierList");
const FixedModifiersList_1 = require("../Modifier/FixedModifier/FixedModifiersList");
class Skill {
    static calculateTrainedPoints(level = 1) {
        if (level <= 6) {
            return 2;
        }
        if (level <= 14) {
            return 4;
        }
        return 6;
    }
    static calculateTrainingPoints(level = 1, isTrained = false) {
        if (!isTrained) {
            return 0;
        }
        return Skill.calculateTrainedPoints(level);
    }
    static calculateLevelPoints(level) {
        return Math.floor(level / 2);
    }
    static get repeatedOtherModifierError() {
        return 'REPEATED_OTHER_SKILL_MODIFIER';
    }
    constructor(params) {
        this.contextualModifiers = new ContextualModifierList_1.ContextualModifiersList();
        this.fixedModifiers = new FixedModifiersList_1.FixedModifiersList();
        this.isTrained = Boolean(params.isTrained);
        this.attribute = params.attribute;
        this.defaultAttribute = params.attribute;
        this.name = params.name;
    }
    changeAttribute(attribute) {
        this.attribute = attribute;
    }
    addContextualModifier(modifier) {
        this.contextualModifiers.add(modifier);
    }
    addFixedModifier(modifier) {
        this.fixedModifiers.add(modifier);
    }
    train() {
        if (this.isTrained) {
            throw new SheetBuilderError_1.SheetBuilderError('TRAINING_TRAINED_SKILL');
        }
        this.isTrained = true;
    }
    getIsTrained() {
        return this.isTrained;
    }
    getTotal(calculator) {
        return calculator.calculate(this);
    }
    getTrainingPoints(level = 1) {
        return Skill.calculateTrainingPoints(level, this.isTrained);
    }
    getLevelPoints(level = 1) {
        return Skill.calculateLevelPoints(level);
    }
    getAttributeModifier(attributes) {
        return attributes[this.attribute];
    }
    serialize(totalCalculator, sheet, context) {
        return {
            attribute: this.attribute,
            contextualModifiers: this.contextualModifiers.serialize(sheet, context),
            fixedModifiers: this.fixedModifiers.serialize(sheet, context),
            isTrained: this.getIsTrained(),
            total: this.getTotal(totalCalculator),
            trainingPoints: this.getTrainingPoints(),
            defaultAttribute: this.defaultAttribute,
        };
    }
}
exports.Skill = Skill;
