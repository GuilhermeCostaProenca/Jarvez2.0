"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Modifiers = void 0;
const ContextualModifier_1 = require("./ContextualModifier");
const FixedModifier_1 = require("./FixedModifier");
const PerLevelModifier_1 = require("./PerLevelModifier");
class Modifiers {
    constructor(params = {}) {
        var _a, _b, _c;
        this.fixed = (_a = params.fixed) !== null && _a !== void 0 ? _a : new FixedModifier_1.FixedModifiersList();
        this.contextual = (_b = params.contextual) !== null && _b !== void 0 ? _b : new ContextualModifier_1.ContextualModifiersList();
        this.perLevel = (_c = params.perLevel) !== null && _c !== void 0 ? _c : new PerLevelModifier_1.PerLevelModifiersList();
    }
    clone() {
        return new Modifiers({
            fixed: this.fixed.clone(),
            contextual: this.contextual.clone(),
            perLevel: this.perLevel.clone(),
        });
    }
    getTotal({ contextCalculator, fixedCalculator, perLevelCalculator, }) {
        return this.fixed.getTotal(fixedCalculator)
            + this.contextual.getTotal(contextCalculator)
            + this.perLevel.getTotal(perLevelCalculator);
    }
    getMaxTotal(attributes, { fixedCalculator, perLevelCalculator, }) {
        return this.fixed.getTotal(fixedCalculator)
            + this.contextual.getMaxTotal(attributes)
            + this.perLevel.getTotal(perLevelCalculator);
    }
    serialize(sheet, context) {
        return {
            fixed: this.fixed.serialize(sheet, context),
            contextual: this.contextual.serialize(sheet, context),
            perLevel: this.perLevel.serialize(sheet, context),
        };
    }
}
exports.Modifiers = Modifiers;
