"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SheetPoints = void 0;
const PointsMaxCalculatorFactory_1 = require("../Points/PointsMaxCalculatorFactory");
class SheetPoints {
    constructor(points) {
        this.points = points;
    }
    serialize(sheet, context) {
        const attributes = sheet.getSheetAttributes().getValues();
        const level = sheet.getLevel();
        return {
            max: this.getMax(attributes, level),
            fixedModifiers: this.getFixedModifiers().serialize(sheet, context),
            perLevelModifiers: this.getPerLevelModifiers().serialize(sheet, context),
        };
    }
    getFixedModifiers() {
        return this.points.fixedModifiers;
    }
    getPerLevelModifiers() {
        return this.points.perLevelModifiers;
    }
    getModifiers() {
        return [
            ...this.points.fixedModifiers.modifiers,
            ...this.points.perLevelModifiers.modifiers,
        ];
    }
    addFixedModifier(modifier) {
        this.points.addModifier(modifier);
    }
    addPerLevelModifier(modifier) {
        this.points.addPerLevelModifier(modifier);
    }
    getMax(attributes, level) {
        const calculator = PointsMaxCalculatorFactory_1.PointsMaxCalculatorFactory.make(attributes, level);
        return this.points.getMax(calculator);
    }
}
exports.SheetPoints = SheetPoints;
