"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.CharacterAttack = void 0;
const Attack_1 = require("../Attack");
const ManaCost_1 = require("../ManaCost");
const Modifier_1 = require("../Modifier");
const Random_1 = require("../Random");
const CharacterAttackTriggeredEffect_1 = require("./CharacterAttackTriggeredEffect");
const CharactterAttackModifiers_1 = require("./CharactterAttackModifiers");
class CharacterAttack {
    constructor(params) {
        const { modifiers, attributes, maxTotalCalculators, skills, totalCalculators, weapon } = params;
        this.modifiers = new CharactterAttackModifiers_1.CharacterAttackModifiers(modifiers);
        this.attack = new Attack_1.WeaponAttack(weapon);
        this.damageAttributeModifierIndex = this.addDamageAttributeFixedModifier(attributes);
        this.totalCalculators = totalCalculators;
        this.maxTotalCalculators = maxTotalCalculators;
        this.attributes = attributes;
        this.skills = skills;
        this.triggeredEffects = new Map();
        params.triggeredEffects.forEach((effect, effectName) => {
            this.triggeredEffects.set(effectName, new CharacterAttackTriggeredEffect_1.CharacterAttackTriggeredEffect(effect, this.modifiers));
        });
    }
    changeTestAttackAttribute(attribute) {
        const skillName = this.attack.getTestDefaultSkill();
        const customTestAttributes = this.attack.getCustomTestAttributes();
        const allowed = customTestAttributes.has(attribute) || attribute === this.skills[skillName].skill.attribute;
        if (!allowed) {
            throw new Error('INVALID_ATTRIBUTE');
        }
        this.skills[skillName].changeAttribute(attribute);
    }
    getDefaultTestSkill() {
        return this.skills[this.attack.getTestDefaultSkill()];
    }
    roll(random = new Random_1.Random()) {
        const skill = this.skills[this.attack.getTestDefaultSkill()];
        const { damage, test } = this.attack.roll(random, skill);
        const damageModifiersTotal = this.getDamageModifiersTotal();
        const testModifiersTotal = this.getTestModifiersTotal();
        return {
            damage: {
                rollResult: damage,
                modifiers: this.modifiers.damage,
                modifiersTotal: damageModifiersTotal,
                total: damage.total + this.getDamageModifiersTotal(),
            },
            test: {
                rollResult: test.roll,
                modifiers: this.modifiers.test,
                modifiersTotal: testModifiersTotal,
                total: test.total + this.getTestModifiersTotal(),
            },
            isCritical: test.isCritical,
            isFumble: test.isFumble,
        };
    }
    enableTriggeredEffect(activation) {
        const effect = this.triggeredEffects.get(activation.effectName);
        if (!effect) {
            throw new Error('INVALID_TRIGGERED_EFFECT');
        }
        effect.enable(activation);
    }
    disableTriggeredEffect(effectName) {
        const effect = this.triggeredEffects.get(effectName);
        if (!effect) {
            throw new Error('INVALID_TRIGGERED_EFFECT');
        }
        effect.disable();
    }
    getTestModifiersMaxTotal() {
        return this.modifiers.test.getMaxTotal(this.attributes, this.maxTotalCalculators);
    }
    getTestModifiersTotal() {
        return this.modifiers.test.getTotal(this.totalCalculators);
    }
    getDamageModifiersMaxTotal() {
        return this.modifiers.damage.getMaxTotal(this.attributes, this.maxTotalCalculators);
    }
    getDamageModifiersTotal() {
        return this.modifiers.damage.getTotal(this.totalCalculators);
    }
    getTriggeredEffects() {
        return this.triggeredEffects;
    }
    getManaCost() {
        let sum = 0;
        this.triggeredEffects.forEach(effect => {
            var _a, _b;
            if (effect.getIsEnabled()) {
                sum += (_b = (_a = effect.getManaCost()) === null || _a === void 0 ? void 0 : _a.value) !== null && _b !== void 0 ? _b : 0;
            }
        });
        return new ManaCost_1.ManaCost(sum);
    }
    getTestSkillAttributeModifier() {
        const skillAttribute = this.getDefaultTestSkill().skill.attribute;
        return this.attributes[skillAttribute];
    }
    serialize(sheet, context) {
        return {
            attack: this.attack.serialize(),
            defaultSkill: this.attack.getTestDefaultSkill(),
            testSkillAttributeModifier: this.getTestSkillAttributeModifier(),
            manaCost: this.getManaCost().serialize(),
            triggeredEffects: Array.from(this.triggeredEffects.values()).map(effect => effect.serialize(sheet, context)),
            modifiers: {
                test: this.modifiers.test.serialize(sheet, context),
                damage: this.modifiers.damage.serialize(sheet, context),
            },
        };
    }
    addDamageAttributeFixedModifier(attributes) {
        const damageAttribute = this.attack.getDamageAttribute();
        if (damageAttribute) {
            const damageAttributeModifier = new Modifier_1.FixedModifier(damageAttribute, attributes[damageAttribute]);
            return this.modifiers.damage.fixed.add(damageAttributeModifier);
        }
    }
}
exports.CharacterAttack = CharacterAttack;
