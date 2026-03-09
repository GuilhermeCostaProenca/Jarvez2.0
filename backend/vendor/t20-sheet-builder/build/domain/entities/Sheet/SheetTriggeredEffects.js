"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SheetTriggeredEffects = void 0;
class SheetTriggeredEffects {
    constructor() {
        this.effects = {
            attack: new Map(),
            defend: new Map(),
            skillTest: new Map(),
            skillTestExceptAttack: new Map(),
            resistanceTest: new Map(),
        };
    }
    getByEvent(event) {
        return this.effects[event];
    }
    registerEffect(events, effect) {
        events.forEach(event => {
            this.effects[event].set(effect.name, effect);
        });
    }
}
exports.SheetTriggeredEffects = SheetTriggeredEffects;
