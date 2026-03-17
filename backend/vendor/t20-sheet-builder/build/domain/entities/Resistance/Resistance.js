"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Resistance = void 0;
const Modifier_1 = require("../Modifier");
class Resistance {
    constructor(resistance, value, source) {
        this.resisted = resistance;
        this.fixedModifiers = new Modifier_1.FixedModifiersList();
        this.fixedModifiers.add(new Modifier_1.FixedModifier(this.resisted, value));
        this.source = source;
    }
    getTotal(attributes) {
        const calculator = new Modifier_1.FixedModifiersListTotalCalculator(attributes);
        return this.fixedModifiers.getTotal(calculator);
    }
    serialize(sheet, context) {
        return {
            resisted: this.resisted,
            fixedModifiers: this.fixedModifiers.serialize(sheet, context),
            source: this.source,
        };
    }
}
exports.Resistance = Resistance;
