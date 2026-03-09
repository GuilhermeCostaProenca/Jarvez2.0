"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DefenseFake = void 0;
const FixedModifiersListFake_1 = require("../Modifier/FixedModifier/FixedModifiersListFake");
class DefenseFake {
    constructor() {
        this.attribute = 'dexterity';
        this.total = 10;
        this.fixedModifiers = new FixedModifiersListFake_1.FixedModifiersListFake();
    }
    getTotal() {
        return this.total;
    }
    addFixedModifier(modifier) {
        this.fixedModifiers.add(modifier);
    }
}
exports.DefenseFake = DefenseFake;
