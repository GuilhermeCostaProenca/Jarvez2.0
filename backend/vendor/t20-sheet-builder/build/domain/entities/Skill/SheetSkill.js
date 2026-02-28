"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SheetSkill = void 0;
const DiceRoll_1 = require("../Dice/DiceRoll");
const Modifier_1 = require("../Modifier");
const Random_1 = require("../Random");
class SheetSkill {
    constructor(skill, calculator) {
        this.skill = skill;
        this.calculator = calculator;
    }
    isTrained() {
        return this.skill.getIsTrained();
    }
    getName() {
        return this.skill.name;
    }
    getFixedModifier(name) {
        return this.skill.fixedModifiers.get(name);
    }
    getContextualModifier(name) {
        return this.skill.contextualModifiers.get(name);
    }
    getModifiersTotal() {
        return this.skill.getTotal(this.calculator);
    }
    getAttributeModifier() {
        return this.skill.getAttributeModifier(this.calculator.baseCalculator.attributes);
    }
    getLevelPoints() {
        return this.skill.getLevelPoints(this.calculator.baseCalculator.level);
    }
    getTrainingPoints() {
        return this.skill.getTrainingPoints(this.calculator.baseCalculator.level);
    }
    getTotalBaseModifier() {
        return this.getAttributeModifier() + this.getLevelPoints() + this.getTrainingPoints();
    }
    changeAttribute(attribute) {
        this.skill.changeAttribute(attribute);
    }
    roll(random = new Random_1.Random(), threat = 20) {
        const rollResult = SheetSkill.test.roll(random);
        return {
            isCritical: rollResult.total >= threat,
            isFumble: rollResult.total <= 1,
            modifiers: new Modifier_1.Modifiers({
                contextual: this.skill.contextualModifiers,
                fixed: this.skill.fixedModifiers,
            }),
            modifiersTotal: this.getModifiersTotal(),
            roll: rollResult,
            total: rollResult.total + this.getModifiersTotal(),
            attributeModifier: this.getAttributeModifier(),
            levelPoints: this.getLevelPoints(),
            trainingPoints: this.getTrainingPoints(),
        };
    }
}
exports.SheetSkill = SheetSkill;
SheetSkill.test = new DiceRoll_1.DiceRoll(1, 20);
