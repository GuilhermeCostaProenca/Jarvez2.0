"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SpecialAttackEffect = void 0;
const TriggeredEffect_1 = require("../../../Ability/TriggeredEffect");
const TriggeredEffectName_1 = require("../../../Ability/TriggeredEffectName");
const ManaCost_1 = require("../../../ManaCost");
const FixedModifier_1 = require("../../../Modifier/FixedModifier/FixedModifier");
const Level_1 = require("../../../Sheet/Level");
const RoleAbilityName_1 = require("../../RoleAbilityName");
const SpecialAttackManaCost_1 = require("./SpecialAttackManaCost");
class SpecialAttackEffect extends TriggeredEffect_1.TriggeredEffect {
    get description() {
        return 'Quando faz um ataque, você pode gastar 1 PM para receber +4 no teste de ataque ou na rolagem de dano. '
            + 'A cada quatro níveis, pode gastar +1 PM para aumentar o bônus em +4. Você pode dividir os bônus igualmente.';
    }
    constructor() {
        super({
            duration: 'next',
            execution: 'reaction',
            source: RoleAbilityName_1.RoleAbilityName.specialAttack,
            triggerEvents: TriggeredEffect_1.TriggerEvent.attack,
            name: TriggeredEffectName_1.TriggeredEffectName.specialAttack,
        });
        this.baseCosts = [new ManaCost_1.ManaCost(1)];
    }
    enable({ modifiersIndexes, modifiers }, activation) {
        var _a;
        const manaCost = new ManaCost_1.ManaCost((_a = activation.mana) !== null && _a !== void 0 ? _a : 1);
        const bonusValue = this.getBonusFromManaCost(manaCost);
        switch (activation.bonus) {
            case 'attack':
                this.enableAttackBonus({ modifiersIndexes, modifiers, bonusValue });
                return { manaCost };
            case 'damage':
                this.enableDamageBonus({ modifiersIndexes, modifiers, bonusValue });
                return { manaCost };
            case 'both':
                this.enableSplittedBonus({ modifiersIndexes, modifiers, bonusValue });
                return { manaCost };
            default:
                this.enableAttackBonus({ modifiersIndexes, modifiers, bonusValue });
                return { manaCost };
        }
    }
    disable({ modifiersIndexes, modifiers }) {
        var _a, _b;
        if (typeof modifiersIndexes.attack === 'number') {
            (_a = modifiers.attack) === null || _a === void 0 ? void 0 : _a.fixed.remove(modifiersIndexes.attack);
        }
        if (typeof modifiersIndexes.damage === 'number') {
            (_b = modifiers.damage) === null || _b === void 0 ? void 0 : _b.fixed.remove(modifiersIndexes.damage);
        }
    }
    enableAttackBonus({ modifiersIndexes, modifiers, bonusValue }) {
        var _a;
        const modifier = new FixedModifier_1.FixedModifier(RoleAbilityName_1.RoleAbilityName.specialAttack, bonusValue);
        modifiersIndexes.attack = (_a = modifiers.attack) === null || _a === void 0 ? void 0 : _a.fixed.add(modifier);
    }
    enableDamageBonus({ modifiersIndexes, modifiers, bonusValue }) {
        var _a;
        const modifier = new FixedModifier_1.FixedModifier(RoleAbilityName_1.RoleAbilityName.specialAttack, bonusValue);
        modifiersIndexes.damage = (_a = modifiers.damage) === null || _a === void 0 ? void 0 : _a.fixed.add(modifier);
    }
    enableSplittedBonus({ modifiersIndexes, modifiers, bonusValue }) {
        var _a, _b;
        const modifier = new FixedModifier_1.FixedModifier(RoleAbilityName_1.RoleAbilityName.specialAttack, bonusValue / 2);
        modifiersIndexes.attack = (_a = modifiers.attack) === null || _a === void 0 ? void 0 : _a.fixed.add(modifier);
        modifiersIndexes.damage = (_b = modifiers.damage) === null || _b === void 0 ? void 0 : _b.fixed.add(modifier);
    }
    getBonusFromManaCost(manaCost) {
        return manaCost.value * 4;
    }
}
exports.SpecialAttackEffect = SpecialAttackEffect;
SpecialAttackEffect.minLevelToCost = {
    [SpecialAttackManaCost_1.SpecialAttackEffectCosts.oneManaPoint]: Level_1.Level.one,
    [SpecialAttackManaCost_1.SpecialAttackEffectCosts.twoManaPoints]: Level_1.Level.five,
};
SpecialAttackEffect.costs = {
    [SpecialAttackManaCost_1.SpecialAttackEffectCosts.oneManaPoint]: new ManaCost_1.ManaCost(1),
    [SpecialAttackManaCost_1.SpecialAttackEffectCosts.twoManaPoints]: new ManaCost_1.ManaCost(2),
};
SpecialAttackEffect.maxModifier = {
    [SpecialAttackManaCost_1.SpecialAttackEffectCosts.oneManaPoint]: 4,
    [SpecialAttackManaCost_1.SpecialAttackEffectCosts.twoManaPoints]: 8,
};
