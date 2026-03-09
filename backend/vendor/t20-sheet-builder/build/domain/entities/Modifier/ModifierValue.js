"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ModifierValue = void 0;
const StringHelper_1 = require("../StringHelper");
class ModifierValue {
    constructor(number) {
        this.number = number;
    }
    getValueWithSign() {
        return StringHelper_1.StringHelper.addNumberSign(this.number);
    }
}
exports.ModifierValue = ModifierValue;
