"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AudacityEffect = void 0;
const Ability_1 = require("../../../Ability");
const ManaCost_1 = require("../../../ManaCost");
const FixedModifier_1 = require("../../../Modifier/FixedModifier/FixedModifier");
const RoleAbilityName_1 = require("../../RoleAbilityName");
class AudacityEffect extends Ability_1.TriggeredEffect {
    constructor() {
        super({
            duration: 'immediate',
            execution: 'reaction',
            name: Ability_1.TriggeredEffectName.audacity,
            source: RoleAbilityName_1.RoleAbilityName.audacity,
            triggerEvents: Ability_1.TriggerEvent.skillTestExceptAttack,
        });
        this.baseCosts = [AudacityEffect.cost];
        this.description = 'Quando faz um teste de perícia,'
            + ' você pode gastar 2 PM para somar seu Carisma no'
            + ' teste. Você não pode usar esta habilidade em testes'
            + ' de ataque.';
    }
    enable({ modifiersIndexes, modifiers }, activation) {
        var _a;
        modifiersIndexes.skillExceptAttack = (_a = modifiers.skillExceptAttack) === null || _a === void 0 ? void 0 : _a.fixed.add(new FixedModifier_1.FixedModifier(this.source, activation.attributes.charisma));
        return {
            manaCost: AudacityEffect.cost,
        };
    }
    disable({ modifiersIndexes, modifiers }) {
        var _a;
        if (typeof modifiersIndexes.skillExceptAttack === 'number') {
            (_a = modifiers.skillExceptAttack) === null || _a === void 0 ? void 0 : _a.fixed.remove(modifiersIndexes.skillExceptAttack);
        }
    }
}
exports.AudacityEffect = AudacityEffect;
AudacityEffect.cost = new ManaCost_1.ManaCost(2);
