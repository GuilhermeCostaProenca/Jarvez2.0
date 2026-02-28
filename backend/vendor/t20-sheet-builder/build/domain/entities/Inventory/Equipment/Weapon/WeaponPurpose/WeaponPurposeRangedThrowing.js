"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.WeaponPurposeRangedThrowing = void 0;
const WeaponPurposeRanged_1 = require("./WeaponPurposeRanged");
class WeaponPurposeRangedThrowing extends WeaponPurposeRanged_1.WeaponPurposeRanged {
    constructor(params = {}) {
        var _a;
        super(Object.assign(Object.assign({}, params), { damageAttribute: (_a = params.damageAttribute) !== null && _a !== void 0 ? _a : 'strength' }));
    }
}
exports.WeaponPurposeRangedThrowing = WeaponPurposeRangedThrowing;
