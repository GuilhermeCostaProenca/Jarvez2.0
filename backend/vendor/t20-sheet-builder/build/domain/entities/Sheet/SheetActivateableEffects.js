"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SheetActivateableEffects = void 0;
class SheetActivateableEffects {
    constructor() {
        this.effects = new Map();
    }
    register(effect) {
        this.effects.set(effect.source, effect);
    }
    getEffects() {
        return this.effects;
    }
    getEffect(source) {
        return this.effects.get(source);
    }
}
exports.SheetActivateableEffects = SheetActivateableEffects;
