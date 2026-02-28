"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.CharacterSkill = void 0;
const DiceRoll_1 = require("../Dice/DiceRoll");
const Modifier_1 = require("../Modifier");
const Random_1 = require("../Random");
const CharacterSkillTriggeredEffect_1 = require("./CharacterSkillTriggeredEffect");
class CharacterSkill {
    constructor(sheetSkill, modifiers, triggeredEffects, modifiersCalculators) {
        this.sheetSkill = sheetSkill;
        this.modifiers = modifiers;
        this.modifiersCalculators = modifiersCalculators;
        this.triggeredEffects = new Map();
        modifiers.skill.fixed.append(this.sheetSkill.skill.fixedModifiers);
        modifiers.skill.contextual.append(this.sheetSkill.skill.contextualModifiers);
        triggeredEffects.forEach((triggeredEffect, name) => {
            this.triggeredEffects.set(name, new CharacterSkillTriggeredEffect_1.CharacterSkillTriggeredEffect(triggeredEffect, modifiers));
        });
    }
    getName() {
        return this.sheetSkill.getName();
    }
    enableTriggeredEffect(activation) {
        const triggeredEffect = this.triggeredEffects.get(activation.effectName);
        if (!triggeredEffect) {
            throw new Error(`Triggered effect ${activation.effectName} not found`);
        }
        triggeredEffect.enable(activation);
    }
    disableTriggeredEffect(effectName) {
        var _a;
        if (!this.triggeredEffects.has(effectName)) {
            throw new Error(`Triggered effect ${effectName} not found`);
        }
        (_a = this.triggeredEffects.get(effectName)) === null || _a === void 0 ? void 0 : _a.disable();
    }
    getModifiersTotal(isAttack = false) {
        let total = 0;
        if (!isAttack) {
            total += this.modifiers.skillExceptAttack.getTotal(this.modifiersCalculators);
        }
        total += this.modifiers.skill.getTotal(this.modifiersCalculators);
        return total;
    }
    getAttributeModifier() {
        return this.sheetSkill.getAttributeModifier();
    }
    getLevelPoints() {
        return this.sheetSkill.getLevelPoints();
    }
    getTrainingPoints() {
        return this.sheetSkill.getTrainingPoints();
    }
    getTotalBaseModifier() {
        return this.sheetSkill.getTotalBaseModifier();
    }
    changeAttribute(attribute) {
        this.sheetSkill.changeAttribute(attribute);
    }
    getTriggeredEffects() {
        return this.triggeredEffects;
    }
    getFixedModifier(type, name) {
        return this.modifiers[type].fixed.get(name);
    }
    getContextualModifier(name) {
        return this.sheetSkill.getContextualModifier(name);
    }
    roll(random = new Random_1.Random(), threat = 20, isAttack = false) {
        const skillRollResult = this.sheetSkill.roll(random, threat);
        const fixedModifiers = this.modifiers.skill.fixed.clone();
        if (!isAttack) {
            fixedModifiers.append(this.modifiers.skillExceptAttack.fixed);
        }
        const contextualModifiers = this.modifiers.skill.contextual.clone();
        if (!isAttack) {
            contextualModifiers.append(this.modifiers.skillExceptAttack.contextual);
        }
        fixedModifiers.append(skillRollResult.modifiers.fixed);
        contextualModifiers.append(skillRollResult.modifiers.contextual);
        return {
            isCritical: skillRollResult.isCritical,
            isFumble: skillRollResult.isFumble,
            roll: skillRollResult.roll,
            modifiers: new Modifier_1.Modifiers({
                fixed: fixedModifiers,
                contextual: contextualModifiers,
            }),
            modifiersTotal: this.getModifiersTotal(isAttack),
            total: skillRollResult.total + this.getModifiersTotal(isAttack),
            attributeModifier: skillRollResult.attributeModifier,
            levelPoints: skillRollResult.levelPoints,
            trainingPoints: skillRollResult.trainingPoints,
        };
    }
}
exports.CharacterSkill = CharacterSkill;
CharacterSkill.test = new DiceRoll_1.DiceRoll(1, 20);
