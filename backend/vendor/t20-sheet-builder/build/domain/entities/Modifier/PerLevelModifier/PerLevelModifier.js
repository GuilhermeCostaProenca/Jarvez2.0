"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.PerLevelModifier = void 0;
const Modifier_1 = require("../Modifier");
class PerLevelModifier extends Modifier_1.Modifier {
    constructor(params) {
        var _a, _b;
        super(Object.assign(Object.assign({}, params), { type: 'perLevel' }));
        this.includeFirstLevel = (_a = params.includeFirstLevel) !== null && _a !== void 0 ? _a : true;
        this.frequency = (_b = params.frequency) !== null && _b !== void 0 ? _b : 1;
    }
    getPerLevelValue() {
        return this.baseValue;
    }
}
exports.PerLevelModifier = PerLevelModifier;
