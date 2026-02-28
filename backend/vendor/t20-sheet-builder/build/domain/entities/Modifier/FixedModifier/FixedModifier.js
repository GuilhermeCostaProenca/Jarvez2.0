"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.FixedModifier = void 0;
const Modifier_1 = require("../Modifier");
class FixedModifier extends Modifier_1.Modifier {
    constructor(source, value, attributeBonuses) {
        super({
            source,
            value,
            attributeBonuses,
            type: 'fixed',
        });
    }
}
exports.FixedModifier = FixedModifier;
