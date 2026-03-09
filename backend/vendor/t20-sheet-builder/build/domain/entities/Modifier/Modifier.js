"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Modifier = void 0;
class Modifier {
    constructor(params) {
        this.source = params.source;
        this.baseValue = params.value;
        this.type = params.type;
        this.attributeBonuses = params.attributeBonuses ? [...params.attributeBonuses] : [];
    }
    getAppliableValue(calculator) {
        return calculator.calculate(this.baseValue, this.attributeBonuses);
    }
    getTotalAttributeBonuses(attributes) {
        return this.attributeBonuses.reduce((acc, attribute) => attributes[attribute] + acc, 0);
    }
    serialize(appliableValueCalculator, attributes) {
        return {
            source: this.source,
            type: this.type,
            attributeBonuses: this.attributeBonuses,
            baseValue: this.baseValue,
            appliableValue: this.getAppliableValue(appliableValueCalculator),
            totalAttributeBonuses: this.getTotalAttributeBonuses(attributes),
        };
    }
}
exports.Modifier = Modifier;
