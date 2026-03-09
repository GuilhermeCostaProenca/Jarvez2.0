"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ModifiersList = void 0;
class ModifiersList {
    constructor() {
        this.modifiers = [];
    }
    getTotal(totalCalculator) {
        return totalCalculator.calculate(this.modifiers);
    }
    add(...modifier) {
        const nextIndex = this.modifiers.push(...modifier);
        return nextIndex - 1;
    }
    append(modifiersList) {
        this.modifiers.push(...modifiersList.modifiers);
    }
    remove(index) {
        this.modifiers.splice(index, 1);
    }
    get(source) {
        return this.modifiers.find(modifier => modifier.source === source);
    }
    clone() {
        const list = new this.constructor();
        this.modifiers.forEach(modifier => list.add(modifier));
        return list;
    }
}
exports.ModifiersList = ModifiersList;
