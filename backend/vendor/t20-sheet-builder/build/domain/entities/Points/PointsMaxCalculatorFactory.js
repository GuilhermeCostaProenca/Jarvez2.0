"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.PointsMaxCalculatorFactory = void 0;
const FixedModifiersListTotalCalculator_1 = require("../Modifier/FixedModifier/FixedModifiersListTotalCalculator");
const PerLevelModifiersListTotalCalculator_1 = require("../Modifier/PerLevelModifier/PerLevelModifiersListTotalCalculator");
const PointsMaxCalculator_1 = require("./PointsMaxCalculator");
class PointsMaxCalculatorFactory {
    static make(attributes, level) {
        const fixedCalculator = new FixedModifiersListTotalCalculator_1.FixedModifiersListTotalCalculator(attributes);
        const perLevelCalculator = new PerLevelModifiersListTotalCalculator_1.PerLevelModifiersListTotalCalculator(attributes, level);
        return new PointsMaxCalculator_1.PointsMaxCalculator(fixedCalculator, perLevelCalculator);
    }
}
exports.PointsMaxCalculatorFactory = PointsMaxCalculatorFactory;
