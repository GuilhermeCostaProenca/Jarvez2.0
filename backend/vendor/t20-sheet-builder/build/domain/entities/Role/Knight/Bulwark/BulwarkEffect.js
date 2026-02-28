"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.BulwarkEffect = void 0;
const Ability_1 = require("../../../Ability");
const ManaCost_1 = require("../../../ManaCost");
const Modifier_1 = require("../../../Modifier");
const RoleAbilityName_1 = require("../../RoleAbilityName");
class BulwarkEffect extends Ability_1.TriggeredEffect {
    constructor() {
        super({
            duration: 'next',
            execution: 'reaction',
            name: Ability_1.TriggeredEffectName.bulwark,
            source: RoleAbilityName_1.RoleAbilityName.bulwark,
            triggerEvents: [Ability_1.TriggerEvent.defend, Ability_1.TriggerEvent.resistanceTest],
        });
        this.baseCosts = [new ManaCost_1.ManaCost(1)];
        this.description = 'Quando sofre um ataque ou faz'
            + ' um teste de resistência, você pode gastar 1 PM'
            + ' para receber +2 na Defesa e nos testes de resistência'
            + ' até o início do seu próximo turno. A cada'
            + ' quatro níveis, pode gastar +1 PM para aumentar'
            + ' o bônus em +2.';
    }
    enable({ modifiersIndexes, modifiers }, activation) {
        var _a;
        modifiersIndexes.defense = (_a = modifiers.defense) === null || _a === void 0 ? void 0 : _a.fixed.add(new Modifier_1.FixedModifier(this.source, 2));
        return {
            manaCost: new ManaCost_1.ManaCost(1),
        };
    }
    disable({ modifiersIndexes, modifiers }) {
        var _a;
        if (typeof modifiersIndexes.defense !== 'undefined') {
            (_a = modifiers.defense) === null || _a === void 0 ? void 0 : _a.fixed.remove(modifiersIndexes.defense);
            modifiersIndexes.defense = undefined;
        }
    }
}
exports.BulwarkEffect = BulwarkEffect;
