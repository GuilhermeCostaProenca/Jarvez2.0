"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AbilityEffect = void 0;
class AbilityEffect {
    constructor(type, source) {
        this.type = type;
        this.source = source;
    }
    serialize() {
        return {
            description: this.description,
        };
    }
}
exports.AbilityEffect = AbilityEffect;
