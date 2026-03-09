"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.IngenuityEffect = void 0;
const Ability_1 = require("../../../Ability");
const ManaCost_1 = require("../../../ManaCost");
const Modifier_1 = require("../../../Modifier");
const RoleAbilityName_1 = require("../../RoleAbilityName");
class IngenuityEffect extends Ability_1.TriggeredEffect {
    constructor() {
        super({
            duration: 'immediate',
            execution: 'reaction',
            name: Ability_1.TriggeredEffectName.ingenuity,
            source: RoleAbilityName_1.RoleAbilityName.ingenuity,
            triggerEvents: [Ability_1.TriggerEvent.skillTestExceptAttack],
        });
        this.baseCosts = [new ManaCost_1.ManaCost(2)];
        this.description = 'Quando faz um teste de'
            + ' perícia, você pode gastar 2 PM para somar a sua Inteligência'
            + ' no teste. Você não pode usar esta habilidade'
            + ' em testes de ataque.';
    }
    enable({ modifiersIndexes, modifiers }, activation) {
        var _a;
        modifiersIndexes.skillExceptAttack = (_a = modifiers.skillExceptAttack) === null || _a === void 0 ? void 0 : _a.fixed.add(new Modifier_1.FixedModifier(this.source, 0, new Set(['intelligence'])));
        return {
            manaCost: new ManaCost_1.ManaCost(2),
        };
    }
    disable({ modifiersIndexes, modifiers }) {
        var _a;
        if (modifiersIndexes.skillExceptAttack) {
            (_a = modifiers.skillExceptAttack) === null || _a === void 0 ? void 0 : _a.fixed.remove(modifiersIndexes.skillExceptAttack);
        }
        modifiersIndexes.skillExceptAttack = undefined;
    }
}
exports.IngenuityEffect = IngenuityEffect;
