"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.WeaponPurpose = void 0;
class WeaponPurpose {
    constructor(params) {
        var _a, _b;
        this.penalty = (_a = params.penalty) !== null && _a !== void 0 ? _a : 0;
        this.customTestAttributes = (_b = params.customTestAttributes) !== null && _b !== void 0 ? _b : new Set();
        this.damageAttribute = params.damageAttribute;
        this.defaultSkill = params.defaultSkill;
    }
}
exports.WeaponPurpose = WeaponPurpose;
