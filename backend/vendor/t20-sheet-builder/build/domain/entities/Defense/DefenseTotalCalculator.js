"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DefenseTotalCalculator = void 0;
class DefenseTotalCalculator {
    constructor(baseCalculator, fixedCalculator) {
        this.baseCalculator = baseCalculator;
        this.fixedCalculator = fixedCalculator;
    }
    calculate(attribute, fixedModifiers) {
        return this.baseCalculator.calculate(attribute)
            + fixedModifiers.getTotal(this.fixedCalculator);
    }
}
exports.DefenseTotalCalculator = DefenseTotalCalculator;
