"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SheetResistences = void 0;
const Resistance_1 = require("../Resistance/Resistance");
class SheetResistences {
    constructor() {
        this.resistances = {};
    }
    addResistance(resistance, value, source) {
        this.resistances[resistance] = new Resistance_1.Resistance(resistance, value, source);
    }
    getTotal(resistance, attributes) {
        const foundResistance = this.resistances[resistance];
        if (foundResistance) {
            return foundResistance.getTotal(attributes);
        }
        return 0;
    }
    getResistances() {
        return this.resistances;
    }
    serialize(sheet, context) {
        const serializedResistencies = {};
        Object.values(this.resistances).forEach(resistance => {
            serializedResistencies[resistance.resisted] = resistance.serialize(sheet, context);
        });
        return {
            resistances: serializedResistencies,
        };
    }
}
exports.SheetResistences = SheetResistences;
