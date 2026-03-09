"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.PointsMaxCalculator = void 0;
class PointsMaxCalculator {
    constructor(fixedModifiersCalculator, perLevelModifiersCalculator) {
        this.fixedModifiersCalculator = fixedModifiersCalculator;
        this.perLevelModifiersCalculator = perLevelModifiersCalculator;
    }
    calculate(fixedModifiers, perLevelModifiers) {
        return fixedModifiers.getTotal(this.fixedModifiersCalculator)
            + perLevelModifiers.getTotal(this.perLevelModifiersCalculator);
    }
}
exports.PointsMaxCalculator = PointsMaxCalculator;
