"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ActivateableAbilityEffect = void 0;
const ManaCost_1 = require("../ManaCost");
const AbilityEffect_1 = require("./AbilityEffect");
class ActivateableAbilityEffect extends AbilityEffect_1.AbilityEffect {
    get activationType() {
        return 'free';
    }
    constructor(params) {
        super('active', params.source);
        this.executionType = params.execution;
        this.duration = params.duration;
    }
    getManaCost() {
        return this.baseCosts.reduce((total, cost) => {
            if (cost instanceof ManaCost_1.ManaCost) {
                return total + cost.value;
            }
            return total;
        }, 0);
    }
}
exports.ActivateableAbilityEffect = ActivateableAbilityEffect;
