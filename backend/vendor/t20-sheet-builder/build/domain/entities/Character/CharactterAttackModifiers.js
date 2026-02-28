"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.CharacterAttackModifiers = void 0;
const Modifiers_1 = require("../Modifier/Modifiers");
class CharacterAttackModifiers {
    constructor(params = {}) {
        var _a, _b;
        const { test, damage } = params;
        this.test = (_a = test === null || test === void 0 ? void 0 : test.clone()) !== null && _a !== void 0 ? _a : new Modifiers_1.Modifiers();
        this.damage = (_b = damage === null || damage === void 0 ? void 0 : damage.clone()) !== null && _b !== void 0 ? _b : new Modifiers_1.Modifiers();
    }
}
exports.CharacterAttackModifiers = CharacterAttackModifiers;
