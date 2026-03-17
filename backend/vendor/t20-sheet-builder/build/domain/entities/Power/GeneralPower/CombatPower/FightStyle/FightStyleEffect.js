"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.FightStyleEffect = void 0;
const ActivateableAbilityEffect_1 = require("../../../../Ability/ActivateableAbilityEffect");
class FightStyleEffect extends ActivateableAbilityEffect_1.ActivateableAbilityEffect {
    constructor(source) {
        super({
            duration: 'immediate',
            execution: 'free',
            source,
        });
        this.baseCosts = [];
    }
}
exports.FightStyleEffect = FightStyleEffect;
