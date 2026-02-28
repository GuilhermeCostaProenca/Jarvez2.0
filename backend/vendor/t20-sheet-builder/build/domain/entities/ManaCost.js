"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ManaCost = void 0;
class ManaCost {
    constructor(value) {
        this.value = value;
        this.type = 'mana';
    }
    serialize() {
        return {
            type: this.type,
            value: this.value,
        };
    }
}
exports.ManaCost = ManaCost;
