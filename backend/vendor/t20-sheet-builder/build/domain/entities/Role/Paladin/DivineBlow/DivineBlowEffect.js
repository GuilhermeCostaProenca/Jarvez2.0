"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DivineBlowEffect = void 0;
const Ability_1 = require("../../../Ability");
const ManaCost_1 = require("../../../ManaCost");
const Modifier_1 = require("../../../Modifier");
const RoleAbilityName_1 = require("../../RoleAbilityName");
class DivineBlowEffect extends Ability_1.TriggeredEffect {
    constructor() {
        super({
            duration: 'immediate',
            execution: 'reaction',
            name: Ability_1.TriggeredEffectName.divineBlow,
            source: RoleAbilityName_1.RoleAbilityName.divineBlow,
            triggerEvents: Ability_1.TriggerEvent.attack,
        });
        this.baseCosts = [new ManaCost_1.ManaCost(2)];
        this.description = 'Quando faz um ataque corpo a'
            + ' corpo, você pode gastar 2 PM para desferir um golpe'
            + ' destruidor. Você soma seu Carisma no teste de ataque'
            + ' e +1d8 na rolagem de dano. A cada quatro níveis, pode'
            + ' gastar +1 PM para aumentar o dano em +1d8.';
    }
    enable({ modifiersIndexes, modifiers }, activation) {
        var _a;
        const index = (_a = modifiers.attack) === null || _a === void 0 ? void 0 : _a.fixed.add(new Modifier_1.FixedModifier(RoleAbilityName_1.RoleAbilityName.divineBlow, 0, new Set(['charisma'])));
        modifiersIndexes.attack = index;
        return {
            manaCost: new ManaCost_1.ManaCost(this.getManaCost()),
        };
    }
    disable({ modifiersIndexes, modifiers }) {
        var _a;
        if (modifiersIndexes.attack) {
            (_a = modifiers.attack) === null || _a === void 0 ? void 0 : _a.fixed.remove(modifiersIndexes.attack);
        }
    }
}
exports.DivineBlowEffect = DivineBlowEffect;
