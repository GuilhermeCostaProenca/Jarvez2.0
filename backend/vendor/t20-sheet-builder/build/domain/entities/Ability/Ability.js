"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Ability = void 0;
const RegisterActivateableEffect_1 = require("../Action/RegisterActivateableEffect");
const RegisterTriggeredEffect_1 = require("../Action/RegisterTriggeredEffect");
class Ability {
    constructor(name, abilityType) {
        this.name = name;
        this.abilityType = abilityType;
    }
    addToSheet(transaction) {
        this.applyPassiveEffects(transaction);
        this.registerTriggeredEffects(transaction);
        this.registerActivateableEffects(transaction);
    }
    applyPassiveEffects(transaction) {
        Object.values(this.effects.passive).forEach(effect => {
            effect.apply(transaction);
        });
    }
    registerTriggeredEffects(transaction) {
        Object.values(this.effects.triggered).forEach(effect => {
            const action = new RegisterTriggeredEffect_1.RegisterTriggeredEffect({
                payload: {
                    effect,
                    events: effect.triggerEvents,
                },
                transaction,
            });
            transaction.run(action);
        });
    }
    registerActivateableEffects(transaction) {
        Object.values(this.effects.activateable).forEach(effect => {
            const action = new RegisterActivateableEffect_1.RegisterActivateableEffect({
                payload: {
                    effect,
                },
                transaction,
            });
            transaction.run(action);
        });
    }
}
exports.Ability = Ability;
